#!/usr/bin/env python3
"""Run a bounded staged current-skill smoke.

This is repo/dev harness tooling. It preserves the public `/daee-epistemics`
surface and writes staged scratch artifacts under `.daee/`. The no-model
self-test proves only harness wiring; it does not prove model behavior.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import build_staged_governed_output as staged_output
from check_field_witness_convergence import registers_in_text as checker_field_witness_registers_in_text
from closure_witness_lib import extract_embedded_field_witness, extract_field_witness, parse_closure_witness, status_head
from delta_result_vocabulary import (
    DELTA_RESULT_VOCABULARY,
    FAMILY_EXECUTION_OWNER_IDS,
    OWNER_OPERATION_VOCABULARY,
    canonical_delta_owner,
    delta_result_vocabulary_errors,
    family_alias_execution_owner,
    family_alias_as_executable_owner_errors,
    owner_operation_delta_result_errors,
    owner_operation_vocabulary_errors,
    route_owner_vocabulary_errors,
    route_owner_family_hint_execution_owner,
    source_formal_delta_operation_errors,
    source_pressure_delta_errors,
)
from register_axis_contract import canonicalize_register_axis, register_axis_floor
from stage05_basis_contract import normalize_terminal_detail_basis


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPLAY_RECORD = (
    ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
)
DEFAULT_INPUT = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "cases"
    / "a9-science-source"
    / "input.txt"
)

STAGE_ORDER = [
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
]

ACT_BODY_REF_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")
SUP_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
ASCII_TO_SUP_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
ASCII_TO_SUB_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
ACT_ROW_DETAIL_RE = re.compile(
    r"^\s*⟦ACT\s+(?P<body_ref>[^\s\[]+)"
    r"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    r"\s*::\s*π=(?P<pressure>[^\n]+?)"
    r"\s*::\s*body_ref=(?P<body_ref_field>[^\s\[:⟧]+)"
    r"\s*::\s*Δ=(?P<delta>[^:\s]+):(?P<delta_result>.+?)"
    r"\s*::\s*(?P<land>Land\([^)\n]+\)\+?)⟧\s*$"
)
ACT_ROW_OWNER_QUALIFIED_BODY_REF_RE = re.compile(
    r"^\s*⟦ACT\s+(?P<body_ref>[^\s\[]+)"
    r"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    r"\s*::\s*π=(?P<pressure>[^\n]+?)"
    r"\s*::\s*body_ref=(?P<body_ref_field>[^\s\[:⟧]+)"
    r"\[(?P<body_ref_owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<body_ref_operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    r"\s*::\s*Δ=(?P<delta>[^:\s]+):(?P<delta_result>.+?)"
    r"\s*::\s*(?P<land>Land\([^)\n]+\)\+?)⟧\s*$"
)
LAND_TARGET_RE = re.compile(r"Land\((?P<target>[^)\n]+)\)")
CANONICAL_BURDEN_ID_RE = re.compile(r"(?<![A-Za-z0-9_])B([1-9][0-9]*)(?![A-Za-z0-9_])")
PUBLIC_ASCII_SUBMOVE_RE = re.compile(r"\bB([1-9][0-9]*)[_\.]([1-9][0-9]*)(\[[^\]\n]+\])?")
PUBLIC_ASCII_BURDEN_RE = re.compile(r"\bB([1-9][0-9]*)\b")
PUBLIC_ASCII_EDGE_RE = re.compile(r"\bB([1-9][0-9]*)\s*(?:->|→)\s*B([1-9][0-9]*)\b")
PUBLIC_ASCII_EDGE_REFERENCE_RE = re.compile(
    r"\b(?P<article>(?:a|an|the)\s+)?"
    r"(?P<source>B[1-9][0-9]*)\s*(?:->|→)\s*"
    r"(?P<target>B[1-9][0-9]*)"
    r"(?:\s+(?P<kind>graph\s+edge|edge|route))?\b",
    re.IGNORECASE,
)
PUBLIC_SUP_EDGE_REFERENCE_RE = re.compile(
    r"\b(?P<article>(?:a|an|the)\s+)?"
    r"(?P<source>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s*(?:->|→)\s*"
    r"(?P<target>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)"
    r"(?:\s+(?P<kind>graph\s+edge|edge|route))?\b",
    re.IGNORECASE,
)
PUBLIC_ASCII_LAND_RE = re.compile(r"\b(Land|HOLD)\(B([1-9][0-9]*)\)", re.IGNORECASE)
PUBLIC_ASCII_MRP_RE = re.compile(r"\bMRP\(B([1-9][0-9]*)\)")
PUBLIC_MACHINE_PAYLOAD_LINE_RE = re.compile(
    r"^\s*(?:[`]{3}|[{[\]},]|"
    r"\"(?:B_LA|B_MRP|B_total|nodes|edges|terminal_states|owner_activations|"
    r"field_witness|coverage_proof|body_ref|burden_id|source|target|from|to|graph)\"\s*:)"
)
STAGE05_TERMINAL_BURDEN_ID_RE = re.compile(r"^B[1-9][0-9]*$")
BODY_REF_BURDEN_RE = re.compile(r"^(?P<burden>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B[1-9][0-9]*)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.][1-9][0-9]*)?$")
ASCII_BODY_REF_RE = re.compile(r"^(?P<burden>[1-9][0-9]*)B[1-9][0-9]*$")
STAGE05_REREAD_PREFIX_RE = re.compile(r"^R\(H,\s*(?:Delta(?:\([^)]*\))?|Δ[^)]*)\)\s*:?\s*")
CONTROLLED_STAGE05_TERMINAL_STATES = {
    "landed",
    "cleared",
    "held-with-reason",
    "carried-PARTIAL",
    "carried-RECURSE",
    "discharged-as-derivative",
}
NEGATIVE_NON_EDGE_REFERENCE_RE = re.compile(
    r"(?i)\b(?:does\s+not|do\s+not|no|without|not)\b"
    r"(?:(?!\n).){0,120}\b(?:license|create|creating|generate|generating|new|extra|downstream|edge|route)\b"
)
M9_RESULT_TOKEN_OPERATION_MAP = {
    "predicate-separated": "predication-repair",
    "category-separated": "predication-repair",
    "referent-separated": "predication-repair",
    "person-nature-transfer-blocked": "predication-repair",
    "sense-separated": "sense-split",
}
STAGE04_OPERATION_ALIAS_MAP = {
    ("M8", "trace"): "consequence-trace",
    ("P7", "boundary"): "scope-boundary",
}
STAGE04_PROOF_FAMILY_CLASSIFICATION_CARRIER_RE = re.compile(
    r"(?i)\b(?:proof[- ]family[- ]classification[- ]pressure|"
    r"proof[- ]family[- ]carrier[- ]pressure|proof[- ]carrier[- ]tribunal[- ]function)\b"
)
STAGE04_PROOF_FAMILY_LABEL_RE = re.compile(r"(?i)\bproof[- ]family[- ]label\b")
STAGE04_REGISTER_AXIS_FALLBACKS = {
    ("proof-method-audit", "proof-overreach-audit", "H"): "τ",
    ("proof-method-audit", "proof-overreach-audit", "m"): "τ",
    ("proof-method-audit", "proof-route-status-audit", "H"): "τ",
    ("M3", "orphaned-intuition", "m"): "♥",
    ("do-second-loop", "accountability-hujjah-compression", "H"): "κ",
    ("do-second-loop", "coercive-guidance-demand", "H"): "κ",
    ("do-second-loop", "coercive-guidance-demand", "τ"): "κ",
    ("do-second-loop", "fitrah-ayat-baseline", "N"): "ξ",
    ("do-second-loop", "punishment-proportionality-accountability", "m"): "♥",
    ("V2", "proof-burden-order", "H"): "ξ",
    ("V2", "proof-burden-order", "τ"): "ξ",
    ("V2", "reason-role-repair", "σ"): "ξ",
    ("V2", "reconstituting-reason", "m"): "ξ",
}


def ordering_owner_family(owner: str) -> str:
    """Return the checker-owned owner family used for ordering comparisons."""

    raw = str(owner or "").strip()
    return canonical_delta_owner(raw) or raw


STAGE07_RELEASE_VALIDATION_ORDER = (
    "visible_opening_header",
    "nla_semantic_faithfulness",
    "field_witness_convergence",
    "formal_reread_state_semantics",
    "mid_reread_pressure",
    "mrp_record_surface_parity",
    "mrp_generated_burden",
    "graph_completeness_json",
    "manual_smoke_render_contract",
    "public_burden_grouping",
    "owner_activation_ordering",
)
STAGE07_RELEASE_VALIDATION_KEYS = set(STAGE07_RELEASE_VALIDATION_ORDER)
B5_PROJECTION_REQUIRED_TRUE_FIELDS = (
    "collapse_positive",
    "coverage_complete",
    "diagnostic_completeness",
)
RELEASE_DIVERGENCE_STATES = {"neutral", "non-neutral"}
RELEASE_CURL_STATES = {"null", "resolved", "non-null"}
RELEASE_OUTPUT_MODE_ALIASES = {
    "single": "single-output",
    "single-output": "single-output",
    "compiled": "compiled-output",
    "compiled-output": "compiled-output",
}
TRANSPORT_ATTEMPTS_SCHEMA = "staged-model-subprocess-attempts-v1"
TRANSPORT_RESUME_SCHEMA = "staged-transport-resume-v1"
SEMANTIC_FAILURE_RE = re.compile(
    r"(?i)\b("
    r"assembly error|validator|validation failed|missing required surface|semantic|"
    r"forbidden claim|hash mismatch|section budget|public output"
    r")\b"
)
TRANSPORT_TIMEOUT_RE = re.compile(
    r"(?i)\b("
    r"timed out|timeout|connection reset|connection aborted|stream disconnected|"
    r"network error|temporarily unavailable|service unavailable|gateway timeout"
    r")\b"
)

STAGE_SPECS: dict[str, dict[str, Any]] = {
    "stage-01-intake": {
        "title": "Intake boundary",
        "produces": ["input_digest", "retained_input"],
        "requires": [],
        "instructions": (
            "Restate only the source boundary, case id, input digest, and retained input path. "
            "Do not answer the case yet."
        ),
    },
    "stage-02-layer-a-diagnostic-ir": {
        "title": "Layer A Diagnostic IR",
        "produces": ["burden_floor", "selected_n_frame", "live_registers"],
        "requires": ["input_digest"],
        "instructions": (
            "Identify the selected/held N-frame, the burden floor, and live registers. "
            "The canonical `selected_n_frame` field must be a string token. "
            "The canonical `burden_floor` field must be a JSON array of bare "
            "canonical burden-id strings only, such as [\"B1\", \"B2\"]. Do not put "
            "public labels, superscript burden markers, register axes, slashes, "
            "source labels, or prose in `burden_floor`; put that richer burden "
            "metadata in `burden_floor_details`. The canonical `live_registers` "
            "field must be a JSON array of strings. If richer diagnostic metadata "
            "is useful, put it in "
            "optional detail fields; do not replace the canonical string fields with "
            "objects. `burden_floor_details` should be a list of detail objects; a "
            "keyed object map is compatibility-normalized only when its keys exactly "
            "match the bare `burden_floor` ids and every value preserves burden "
            "identity. Do not attempt filesystem reads or return `status=fail` "
            "because `skill/SKILL.md` is unavailable as a readable path; use the "
            "runtime identity, prompt contract, raw input, and previous validated "
            "stage state supplied by the harness. Do not release a final answer."
        ),
    },
    "stage-03-routing-owner-gate": {
        "title": "Routing / owner gate",
        "produces": ["route_targets", "owner_routes"],
        "requires": ["burden_floor"],
        "instructions": (
            "Route the burden floor to owner/TTP eligibility. Do not activate an owner "
            "unless the route is backed. The canonical `route_targets` field must be a "
            "JSON array of burden-id strings only, such as [\"B1\"]. If richer routing "
            "metadata is useful, put it in optional `route_target_details`; do not put "
            "objects in `route_targets`. The canonical `owner_routes` field must be a "
            "JSON array of objects with string `burden_id` and `owner_id` fields; richer "
            "owner-order evidence may be placed in optional detail fields. Route/context "
            "labels, umbrella family labels, and case-library labels are route context, "
            "not activation proof; later ACT rows must use a callable selected owner/TTP "
            "floor. A route is executable for Stage 04 only when the selected owner "
            "family has source-owned operation and delta_result vocabulary, or when the "
            "`owner_routes` row names a controlled `owner.operation` pair. In the "
            "canonical `owner_routes` object, `owner_id` carries the owner or approved "
            "owner alias, while `operation` / `owner_operation` carries only the "
            "owner-local callable operation token. Do not prefix `operation` with "
            "`owner_id`, an owner alias, a route label, or an ACT display token; for "
            "example use `owner_id: source-status-repair` with `operation: source-order`, "
            "not `operation: source-status-repair.source-order`. If a selected "
            "route has no loaded callable owner body, no controlled operation, or no "
            "owner-local delta_result vocabulary, preserve it as HOLD/PARTIAL with "
            "OWNER-BODY-NOT-LOADED / controlled-vocabulary-gap evidence instead of "
            "converting the route label into a fake ACT owner. Some owner operations "
            "also have operation-specific delta floors. For example, `M8.dependency-trace` "
            "is executable only as the dependency-exposure transition with "
            "`delta_result=dependency-exposed`; use a different callable M8 operation "
            "or HOLD/PARTIAL if the intended transition is not dependency exposure."
        ),
    },
    "stage-04-burden-execution-act": {
        "title": "Burden execution / ACT",
        "produces": ["act_targets", "act_body_refs", "act_rows"],
        "requires": ["route_targets", "owner_routes"],
        "instructions": (
            "Produce canonical ACT handoff evidence for the routed burdens. "
            "`act_targets`, `act_burdens`, `act_body_refs`, and `act_rows` must be JSON "
            "arrays of strings. `act_targets` and `act_burdens` must use canonical "
            "burden-id strings only, such as [\"B1\"], not descriptive burden labels. "
            "Every ACT row must be an exact canonical row beginning "
            "with `⟦ACT`, containing `body_ref=`, `Δ=`, and `Land(`, and closing with "
            "`⟧`. The token immediately after `⟦ACT` is the public owner-qualified "
            "submove token, such as `¹B₁[source-status-repair.source-order]`; the "
            "canonical slot grammar is `⟦ACT <bare-ref>[<owner>.<operation>] :: "
            "π=<pressure> :: body_ref=<same-bare-ref> :: Δ=<delta-id>:<delta_result> "
            ":: Land(<burden>)+⟧`. Do not omit the `::` separators, reorder these "
            "slots, or place `body_ref=` before `π=`. "
            "`<delta-id>` is a transition carrier, not the owner-local result. It must "
            "name a burden-state delta such as `Δ¹B` / `ΔB1` or a dependency-radius "
            "delta such as `Δκ`; never use diagnostic step IDs like `D7`, submove IDs "
            "like `Δ¹B₁` / `ΔB1_1`, owner.operation strings, register axes, or prose "
            "labels before the colon. Put the owner-local state change only after the "
            "colon as `delta_result`, and mirror that suffix in ACT details, NAR, and "
            "field_witness owner activations. "
            "`body_ref=` value and every `act_body_refs[]` item must be only the bare "
            "submove join key before the bracket, such as `¹B₁`. Do not put "
            "`[owner.operation]` in `body_ref=` or `act_body_refs[]`. This keeps the "
            "public ACT row, body_ref dereference, owner_activation mirror, NAR, and "
            "field_witness tied to one stable DSL key while owner and operation remain "
            "separate typed fields. In public Unicode notation, the superscript before "
            "`B` is the burden number and the subscript after `B` is the submove number: "
            "`¹B₁`, `¹B₂`, `¹B₃` are three submoves of burden B1, while `²B₁` is the "
            "first submove of burden B2. Therefore a row whose `Land(...)` target is B1 "
            "must not use `²B₁` or `³B₁` as additional B1 submoves; use `¹B₂` / `¹B₃` "
            "or an approved ASCII fallback such as `B1_2` / `B1_3` in machine-only "
            "fields when the public notation is unavailable. "
            "`act_row_details` is required and must be a JSON array of objects tied to "
            "the exact ACT row with `act_row` and/or the same bare `body_ref`, not "
            "owner-qualified body_ref strings or prose strings. Each detail object must "
            "carry separate `body_ref`, `burden_id`, `owner_id`, `operation`, "
            "`register_axis`, and `delta_result` evidence. `register_axis` must name the "
            "noetic tuple/register field being acted on (`N`, `m`, `τ`, `σ`, `♥`, `ξ`, "
            "`Ω`, `μ`, `κ`, or `H`); it is not a substitute for body_ref, owner, "
            "operation, or delta_result. Source-status operations bind to `σ`; "
            "SOURCE/authority-order operations bind to source/semantic/authority "
            "status (`σ`) or explicitly held source/authority residue (`ξ`), not "
            "`Ω`; do not borrow `Ω` merely because the burden also has ontological "
            "pressure. M9 predication/residue/memetic-carrier repairs bind only "
            "to an approved M9 axis (`μ`, `ξ`, or `Ω`). Do not guess by encoding "
            "the operation into "
            "`body_ref`. The ACT bracket owner token before the dot must be the full "
            "selected owner id, not an abbreviation; long owner ids still use "
            "`full-owner-id.operation` and the detail row mirrors that same `owner_id`. "
            "The operation after the dot must be a controlled callable operation for "
            "that owner family; route pressure and result labels belong in `π=` or "
            "`delta_result`, not in the operation slot. Do not put objects in `act_rows` unless each object also "
            "carries an explicit string `act_row` for harness normalization. "
            "The ACT bracket owner must be a callable selected owner/TTP floor, not a "
            "route/context umbrella label, case-library label, noetic-frame label, or "
            "code lookup. When the selected owner body is unavailable/not loaded, or "
            "when the selected owner has no controlled Stage 04 operation/delta_result "
            "vocabulary, emit HOLD/PARTIAL / OWNER-BODY-NOT-LOADED / "
            "controlled-vocabulary-gap handoff evidence instead of claiming `Land(...)`. "
            "When an owner operation has an operation-specific delta floor, keep that "
            "hidden transition state distinct from the wider owner-family vocabulary. "
            "For `M8.dependency-trace`, `delta_result` must be `dependency-exposed`; "
            "`entailment-blocked` remains an M8-family result for consequence/entailment "
            "work, but it is not a licensed dependency-trace Land transition."
        ),
    },
    "stage-05-mrp-reread-terminal-state": {
        "title": "MRP / reread / terminal state",
        "produces": [
            "terminal_states",
            "dependency_graph_edges",
            "no_new_resultant_proof",
            "per_burden_reread",
        ],
        "requires": ["act_rows"],
        "instructions": (
            "Produce Stage 05 JSON only. Do not write final answer prose, field_witness, "
            "Closing Formulation, release output, verifier sidecars, or proof artifacts. "
            "`terminal_states` must be a JSON object mapping every Stage 04 ACT burden id "
            "to one controlled terminal-state head only: landed, cleared, held-with-reason, "
            "carried-PARTIAL, carried-RECURSE, or discharged-as-derivative. Put burden-local "
            "delta_result/result detail in ACT/NAR/witness detail fields, not in "
            "`terminal_states`; never emit values like `terminal_landed_*` as terminal "
            "states. `dependency_graph_edges` must be a "
            "JSON array; use [] when no dependency edge remains. If no new resultant "
            "burden is live, set `no_new_resultant_proof` to true or to an object "
            "`{\"proved\": true, \"basis\": \"...\", \"unresolved_burdens\": []}`. "
            "If a generated/MRP burden exists, list it under `generated_burdens` and "
            "include it in `terminal_states`. If any burden remains unresolved, return "
            "`status` held or partial, not pass, and expose `unresolved_burdens`. "
            "If `terminal_state_details` is present, each row must name `burden_id` "
            "and a controlled `state` matching `terminal_states[burden_id]`; "
            "`terminal_state` may be normalized to `state` only when the two values "
            "are identical and controlled. "
            "`per_burden_reread` is REQUIRED: a JSON array carrying exactly one object per "
            "`terminal_states` burden id, recording the real post-Land R(H,Δ) reread for that "
            "burden. Required string fields per entry: `burden_id` (machine `B<n>`), `target` "
            "(public burden read, e.g. `¹B / imported tribunal burden`), `reread` (must start "
            "`R(H,` and record `held routes rechecked: ...; live remainder: ...; release/next: ...`), "
            "`landed_delta` (must name Δ/Delta), `route_gradient`, `divergence` "
            "(`<head> / <reason>` with head neutral|settled|bounded|non-neutral), `curl` "
            "(`<head> / <reason>` with head null|resolved|held|non-null), `finding` "
            "(stable|genuine-dependent|partial-real|hidden-framework-recoil|doubt-churn|reorientation), "
            "`route_result_type` (held_burden_activation|generated_burden_instantiation|"
            "no_new_resultant|loopbreak|hold_partial), `mrp_resultant`, `graph_delta` (`none` or "
            "one ASCII edge `Bn -> Bm`), `preemption_basis` (none|graph-bound|commitment-bound|"
            "framework-bound), `route` (STOP|HOLD|RECURSE|LoopBreak(∇×T)), and `boundary` "
            "(must begin `T_lang does not imply guaranteed uptake`). `pressure_activations` must "
            "be an object with exactly the six slots freeze-landed-move, dependency-tug, "
            "hidden-framework-recoil, entailment-pressure, doubt-churn-guard, and "
            "reorientation-reminder; every slot value must record the real pressure read for THIS "
            "burden and begin with the owner/TTP id, `pressure class:`, or `coverage gap:` that "
            "carried it — placeholder values like none/cleared/n/a are rejected. Consistency is "
            "enforced: stable requires route STOP and graph_delta none; genuine-dependent requires "
            "RECURSE and a graph edge; partial-real requires HOLD; any graph edge requires a "
            "non-none preemption_basis. The required boundary prefix is allowed and required; "
            "do not write affirmative uptake-guarantee claims such as `T_lang guarantees uptake`, "
            "`guaranteed T_lang uptake`, or `guarantees interlocutor uptake` in any "
            "`per_burden_reread` string field. "
            "Return one syntactically valid JSON object only: every array item must have exactly "
            "one object-closing brace before a comma, every string quote inside a value must be "
            "escaped, and no prose or second object may appear outside the root object. "
            "The harness renders the public [Mid-Reread Pressure] "
            "blocks from these records; do not write the blocks yourself anywhere."
        ),
    },
    "stage-06-field-witness-nar": {
        "title": "field_witness / NAR",
        "produces": [
            "field_witness_body_refs",
            "nar_burdens",
            "normalized_activation_record",
            "register_deltas",
        ],
        "requires": ["terminal_states", "act_body_refs"],
        "instructions": (
            "Produce Stage 06 JSON only. Do not write a final answer, Restorative Response, "
            "Closing Formulation, sidecars, release output, Grapher output, or certificate "
            "evidence. `field_witness_body_refs` must be a JSON array of strings that exactly "
            "matches Stage 04 `act_body_refs`. `nar_burdens` must include Stage 04 ACT burdens "
            "and every Stage 05 terminal-state burden. `owner_activations` must be body-ref "
            "strings, or objects with explicit string `body_ref` so the harness can normalize "
            "them while preserving details under `owner_activation_details`. Object-shaped "
            "`owner_activations` must include the exact Stage 04 `owner_id`, `operation`, "
            "and owner-local `delta_result` for that same `body_ref`; do not replace "
            "owner-local tokens with generic `delta` arrays. For model-mode "
            "Stage 06, do not use only `normalized_activation_record: true`; provide a "
            "structured `normalized_activation_record` object or `normalized_activation_record_details` "
            "with `n_frame`, `live_registers`, `burden_floor`, and `per_burden`. "
            "`normalized_activation_record.n_frame` must be one non-empty string token. "
            "Do not put `selected`/`held` objects in canonical `n_frame`; if those details "
            "are useful, put them in `n_frame_details` or "
            "`normalized_activation_record_details.n_frame_details`. "
            "When a structured `normalized_activation_record` is present, "
            "`normalized_activation_record_details` is supplemental metadata only; any "
            "`n_frame_details.selected` value there must match the canonical string "
            "`normalized_activation_record.n_frame`. Within any `n_frame_details` object, "
            "`held`, when present, must be a JSON array of held n_frame string tokens only. "
            "Put hold reasons in `held_details` as objects with `n_frame` and `hold_reason`; "
            "each `held_details[].n_frame` must also appear in `held`. Do not put objects "
            "inside `held`. "
            "`per_burden` must be a JSON array/list of objects; each object must include "
            "a non-empty string `burden_id`. When a row mirrors a Stage 04 owner activation, "
            "include `owner_id`, `operation`, and the exact owner-local `delta_result`; "
            "do not emit `per_burden` as a burden-keyed object map. "
            "Top-level `register_deltas` is a required Stage 06 produced field. It must be "
            "parser-stable as an object mapping register names to a non-empty string or "
            "non-empty string array, or as a list of objects with `register` plus `delta` "
            "as a non-empty string or non-empty string array. Do not put register deltas "
            "only inside `normalized_activation_record`; any NAR register-delta mirror is "
            "supplemental and must not replace the top-level Stage 06 field. Any NAR row "
            "carrying `mrp_route_result_type` must match the matching Stage 05 "
            "`per_burden_reread[].route_result_type`. "
            "If Stage 06 cannot honestly mirror ACT/terminal evidence, "
            "return status fail or partial; do not invent witness proof."
        ),
    },
}

HANDOFFS = [
    {
        "from": "stage-01-intake",
        "to": "stage-02-layer-a-diagnostic-ir",
        "checks": ["input_boundary_preserved"],
        "status": "pass",
    },
    {
        "from": "stage-02-layer-a-diagnostic-ir",
        "to": "stage-03-routing-owner-gate",
        "checks": ["burden_floor_to_route_targets", "live_registers_present", "n_frame_present"],
        "status": "pass",
    },
    {
        "from": "stage-03-routing-owner-gate",
        "to": "stage-04-burden-execution-act",
        "checks": ["owner_eligibility_backed", "route_targets_to_act_targets"],
        "status": "pass",
    },
    {
        "from": "stage-04-burden-execution-act",
        "to": "stage-05-mrp-reread-terminal-state",
        "checks": ["act_body_refs_present", "act_rows_present"],
        "status": "pass",
    },
    {
        "from": "stage-05-mrp-reread-terminal-state",
        "to": "stage-06-field-witness-nar",
        "checks": ["dependency_graph_explicit", "terminal_states_to_field_witness"],
        "status": "pass",
    },
    {
        "from": "stage-06-field-witness-nar",
        "to": "stage-07-release-output",
        "checks": ["field_witness_nar_convergence"],
        "status": "pass",
    },
    {
        "from": "stage-07-release-output",
        "to": "stage-08-verifier-sidecars",
        "checks": ["release_to_verifier_sidecars"],
        "status": "pass",
    },
]

NO_MODEL_NON_CLAIMS = {
    "not_model_smoke": True,
    "not_runtime_default_emission_proof": True,
    "not_arbitrary_nl_ir_parser": True,
    "not_package_provenance": True,
    "not_guaranteed_t_lang_uptake": True,
}
MODEL_NON_CLAIMS = {
    "not_model_smoke": False,
    "not_broad_model_behavior": True,
    "not_broad_model_matrix": True,
    "not_runtime_default_emission_proof": True,
    "not_arbitrary_nl_ir_parser": True,
    "not_package_provenance": True,
    "not_guaranteed_t_lang_uptake": True,
    "not_graphify_or_activegraph_proof": True,
}


class HarnessError(Exception):
    """User-facing harness failure."""


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def b5_projection_eligibility_errors(certificate: Any) -> list[str]:
    if not isinstance(certificate, dict):
        return ["collapse certificate root must be a JSON object"]
    errors: list[str] = []
    for key in B5_PROJECTION_REQUIRED_TRUE_FIELDS:
        if certificate.get(key) is not True:
            errors.append(f"{key} must be true before B.5 projection")
    hold_nodes = certificate.get("hold_partial_nodes")
    if hold_nodes not in (None, []):
        errors.append("hold_partial_nodes must be empty before B.5 projection")
    return errors


def write_b5_projection_ineligibility(
    *,
    root: Path,
    certificate_path: Path,
    eligibility_path: Path,
    errors: list[str],
) -> None:
    write_json(
        eligibility_path,
        {
            "eligible": False,
            "source_certificate": rel(certificate_path, root),
            "errors": errors,
            "boundary": (
                "Stage 07-valid HOLD/PARTIAL/RECURSE output is not B.5 proof-projection "
                "eligible until collapse_positive, coverage_complete, and diagnostic_completeness are true."
            ),
            "non_claims": {
                "not_b5_projection_sidecar": True,
                "not_retained_promotion_eligible": True,
                "does_not_weaken_b5_validator": True,
            },
        },
    )


def resolve_under_root(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise HarnessError(f"{label} must resolve inside repo root: {value}") from exc
    return resolved


def run_checked(command: list[str], *, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def require_command_success(command: list[str], *, cwd: Path, input_text: str | None = None) -> str:
    result = run_checked(command, cwd=cwd, input_text=input_text)
    if result.returncode != 0:
        raise HarnessError(
            "Command failed: "
            + " ".join(command)
            + "\n"
            + result.stdout
        )
    return result.stdout


def validate_replay_record(root: Path, replay_record: Path) -> None:
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(replay_record),
        ],
        cwd=root,
    )


def validate_required_files(root: Path) -> dict[str, Path]:
    required = {
        "skill": root / "skill" / "SKILL.md",
        "handshake_checker": root / "tools" / "check_staged_runtime_handshake.py",
        "sidecar_builder": root / "tools" / "build_retained_proof_sidecars.py",
        "b5_sidecar_builder": root / "tools" / "build_b5_full_ir_projection_sidecar.py",
        "nla_checker": root / "tools" / "check_nla_decode_semantic_faithfulness.py",
        "field_witness_checker": root / "tools" / "check_field_witness_convergence.py",
        "formal_reread_checker": root / "tools" / "check_formal_reread_state_semantics.py",
        "graph_checker": root / "tools" / "check_graph_completeness.py",
        "manual_render_checker": root / "tools" / "check_manual_smoke_render_contract.py",
        "public_burden_grouping_checker": root / "tools" / "check_public_burden_grouping.py",
        "owner_ordering_checker": root / "tools" / "check_owner_activation_ordering.py",
    }
    missing = [f"{name}: {path}" for name, path in required.items() if not path.exists()]
    if missing:
        raise HarnessError("Required file(s) missing:\n- " + "\n- ".join(missing))
    return required


def compact_state(stages: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for stage in stages:
        stage_id = stage.get("id")
        if isinstance(stage_id, str):
            result[stage_id] = {
                key: value
                for key, value in stage.items()
                if key not in {"notes", "analysis", "rationale"}
            }
    return result


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Stage response was not a parseable JSON object: json_parse_failure: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HarnessError("Stage response root must be a JSON object")
    return parsed


def normalized_stage(stage_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("id") != stage_id:
        raise HarnessError(f"{stage_id}: response id must be {stage_id!r}")
    status = payload.get("status")
    if status not in {"pass", "held", "partial", "fail"}:
        raise HarnessError(f"{stage_id}: status must be pass, held, partial, or fail")
    stage = dict(payload)
    spec = STAGE_SPECS.get(stage_id)
    if spec is not None:
        stage["produces"] = spec["produces"]
        stage["requires"] = spec["requires"]
    if stage_id == "stage-02-layer-a-diagnostic-ir":
        normalize_stage02_diagnostic_fields(stage)
    if stage_id == "stage-03-routing-owner-gate":
        normalize_stage03_route_targets(stage)
        normalize_stage03_owner_routes(stage)
    if stage_id == "stage-04-burden-execution-act":
        normalize_stage04_act_fields(stage)
    if stage_id == "stage-05-mrp-reread-terminal-state":
        normalize_stage05_mrp_fields(stage)
    if stage_id == "stage-06-field-witness-nar":
        normalize_stage06_witness_nar_fields(stage)
    return stage


def ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def normalization_object(stage: dict[str, Any]) -> dict[str, Any]:
    normalization = stage.get("normalization")
    if not isinstance(normalization, dict):
        normalization = {}
    return normalization


def non_empty_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def delta_token_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def canonical_delta_result_for_owner(
    owner: Any,
    operation: Any,
    pressure: Any,
    raw_delta_result: Any,
) -> str:
    raw = str(raw_delta_result or "").strip()
    if not raw:
        return raw
    family = canonical_delta_owner(str(owner or "")) or str(owner or "").strip().upper()
    vocabulary = DELTA_RESULT_VOCABULARY.get(family)
    if not vocabulary:
        return raw
    if family == "SOURCE":
        pressure_token = delta_token_key(pressure)
        operation_token = str(operation or "").strip()
        proof_text_recoil = (
            "proof-text" in pressure_token
            and ("source-order" in pressure_token or "recoil" in pressure_token)
        )
        generic_hidden_recoil = (
            "hidden-support" in pressure_token
            or ("hidden" in pressure_token and "support" in pressure_token)
            or "source-order-recoil" in pressure_token
            or "future-support" in pressure_token
        )
        if (
            operation_token in {"source-order-repair", "source-order", "sort"}
            and raw in {"source-order-repaired", "proof-text-sorted"}
        ):
            if proof_text_recoil:
                return "proof-text-hidden-support-blocked"
            if generic_hidden_recoil:
                return "hidden-support-blocked"
    if (
        family == "V2"
        and str(operation or "").strip() == "proof-burden-order"
        and raw == "burden-order-repaired"
    ):
        return "proof-burden-order-restored"
    return raw


def require_delta_result_vocabulary(label: str, owner: Any, raw_delta_result: Any) -> None:
    token = str(raw_delta_result or "").strip()
    errors = delta_result_vocabulary_errors(label, str(owner or ""), token)
    if errors:
        raise HarnessError("; ".join(errors))


def canonicalize_delta_fields(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str] | None]:
    owner = item.get("owner") or item.get("owner_id")
    operation = item.get("operation")
    pressure = item.get("pressure")
    raw_result = item.get("delta_result")
    delta_value = str(item.get("delta") or "")
    if not raw_result and ":" in delta_value:
        raw_result = delta_value.split(":", 1)[1]
    canonical = canonical_delta_result_for_owner(owner, operation, pressure, raw_result)
    require_delta_result_vocabulary("delta_result", owner, canonical)
    pair_errors = source_formal_delta_operation_errors("delta_result", owner, operation, canonical)
    if pair_errors:
        raise HarnessError("; ".join(pair_errors))
    pressure_errors = source_pressure_delta_errors("delta_result", owner, pressure, canonical)
    if pressure_errors:
        raise HarnessError("; ".join(pressure_errors))
    if not raw_result or canonical == str(raw_result).strip():
        return item, None
    updated = dict(item)
    updated["delta_result"] = canonical
    if delta_value and ":" in delta_value:
        updated["delta"] = delta_value.split(":", 1)[0] + ":" + canonical
    return updated, {
        "owner": str(owner or ""),
        "operation": str(operation or ""),
        "pressure": str(pressure or ""),
        "raw_delta_result": str(raw_result).strip(),
        "canonical_delta_result": canonical,
    }


def reject_stage04_owner_qualified_body_ref(row: str) -> None:
    match = ACT_ROW_DETAIL_RE.match(row)
    if match and match.group("body_ref") == match.group("body_ref_field"):
        return

    match = ACT_ROW_OWNER_QUALIFIED_BODY_REF_RE.match(row)
    if match:
        raise HarnessError(
            "stage-04 ACT row body_ref must be the bare burden/submove join key; "
            "owner.operation belongs in ACT bracket/object fields, not body_ref"
        )


def require_stage04_register_axis(
    *,
    index: int,
    item: dict[str, Any],
    parsed: dict[str, str],
) -> tuple[str, bool]:
    raw_axis = item.get("register_axis", item.get("axis"))
    axis = canonicalize_register_axis(raw_axis)
    if axis is None:
        raise HarnessError(f"stage-04 act_row_details[{index}].register_axis is required")

    allowed_axes = register_axis_floor(parsed["owner_id"], parsed.get("operation"))
    if allowed_axes is not None and axis not in allowed_axes:
        fallback_axis = STAGE04_REGISTER_AXIS_FALLBACKS.get(
            (parsed["owner_id"], parsed.get("operation") or "", axis)
        )
        if fallback_axis and fallback_axis in allowed_axes:
            return fallback_axis, True
        operation_suffix = f".{parsed.get('operation')}" if parsed.get("operation") else ""
        raise HarnessError(
            f"stage-04 act_row_details[{index}].register_axis {axis!r} is not approved for owner "
            f"{parsed['owner_id']}{operation_suffix}"
        )

    return axis, isinstance(raw_axis, str) and raw_axis.strip() != axis


def canonicalize_stage04_operation_token(
    owner: Any,
    operation: Any,
    pressure: Any = None,
    delta_result: Any = None,
) -> str:
    family = canonical_delta_owner(str(owner or "")) or str(owner or "").strip()
    token = str(operation or "").strip()
    pressure_text = str(pressure or "").strip()
    result_text = str(delta_result or "").strip()
    if (
        family == "PROOF_METHOD"
        and token == "proof-family-classification"
        and result_text == "proof-family-carrier-typed"
        and STAGE04_PROOF_FAMILY_CLASSIFICATION_CARRIER_RE.search(pressure_text)
        and not STAGE04_PROOF_FAMILY_LABEL_RE.search(pressure_text)
    ):
        return "proof-family-and-carrier-audit"
    return STAGE04_OPERATION_ALIAS_MAP.get((family, token), token)


def canonicalize_stage04_act_row(row: str) -> tuple[str, dict[str, str] | None]:
    reject_stage04_owner_qualified_body_ref(row)
    match = ACT_ROW_DETAIL_RE.match(row)
    if not match:
        return row, None
    rewrite: dict[str, str] | None = None
    canonical_operation = canonicalize_stage04_operation_token(
        match.group("owner"),
        match.group("operation"),
        match.group("pressure"),
        match.group("delta_result").strip(),
    )
    if canonical_operation != match.group("operation"):
        start, end = match.span("operation")
        row = row[:start] + canonical_operation + row[end:]
        rewrite = {
            "body_ref": match.group("body_ref"),
            "owner": match.group("owner"),
            "raw_operation": match.group("operation"),
            "canonical_operation": canonical_operation,
        }
        match = ACT_ROW_DETAIL_RE.match(row)
        if not match:
            raise HarnessError("Stage 04 ACT row operation canonicalization produced an unparseable row")
    alias_errors = family_alias_as_executable_owner_errors(
        "Stage 04 ACT row",
        match.group("owner"),
        match.group("operation"),
    )
    if alias_errors:
        raise HarnessError(alias_errors[0])
    operation_errors = owner_operation_vocabulary_errors(
        "Stage 04 ACT row",
        match.group("owner"),
        match.group("operation"),
    )
    if operation_errors:
        raise HarnessError(operation_errors[0])
    raw_result = match.group("delta_result").strip()
    canonical = canonical_delta_result_for_owner(
        match.group("owner"),
        match.group("operation"),
        match.group("pressure"),
        raw_result,
    )
    require_delta_result_vocabulary("Stage 04 ACT row", match.group("owner"), canonical)
    pair_errors = source_formal_delta_operation_errors(
        "Stage 04 ACT row",
        match.group("owner"),
        match.group("operation"),
        canonical,
    )
    if pair_errors:
        raise HarnessError("; ".join(pair_errors))
    operation_delta_errors = owner_operation_delta_result_errors(
        "Stage 04 ACT row",
        match.group("owner"),
        match.group("operation"),
        canonical,
    )
    if operation_delta_errors:
        raise HarnessError("; ".join(operation_delta_errors))
    pressure_errors = source_pressure_delta_errors(
        "Stage 04 ACT row",
        match.group("owner"),
        match.group("pressure"),
        canonical,
    )
    if pressure_errors:
        raise HarnessError("; ".join(pressure_errors))
    if canonical == raw_result:
        return row, rewrite
    start, end = match.span("delta_result")
    row = row[:start] + canonical + row[end:]
    if rewrite is None:
        rewrite = {
            "body_ref": match.group("body_ref"),
            "owner": match.group("owner"),
            "operation": match.group("operation"),
            "pressure": match.group("pressure").strip(),
        }
    rewrite["raw_delta_result"] = raw_result
    rewrite["canonical_delta_result"] = canonical
    return row, rewrite


def canonicalize_stage04_act_rows(rows: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    canonical_rows: list[str] = []
    rewrites: list[dict[str, str]] = []
    for row in rows:
        canonical_row, rewrite = canonicalize_stage04_act_row(row)
        canonical_rows.append(canonical_row)
        if rewrite:
            rewrites.append(rewrite)
    return ordered_unique(canonical_rows), rewrites


def record_stage04_act_row_canonicalizations(
    normalization: dict[str, Any],
    rewrites: list[dict[str, str]],
) -> None:
    if not rewrites:
        return
    operation_rewrites = [rewrite for rewrite in rewrites if "raw_operation" in rewrite]
    delta_rewrites = [rewrite for rewrite in rewrites if "raw_delta_result" in rewrite]
    if operation_rewrites:
        normalization["operation_canonicalizations"] = operation_rewrites
    if delta_rewrites:
        normalization["delta_result_canonicalizations"] = delta_rewrites


def canonical_burden_id_from_text(value: str, allowed_ids: set[str] | None = None) -> str | None:
    text = value.strip()
    if allowed_ids is None or text in allowed_ids:
        if CANONICAL_BURDEN_ID_RE.fullmatch(text):
            return text
    matches = ordered_unique([f"B{match.group(1)}" for match in CANONICAL_BURDEN_ID_RE.finditer(text)])
    if allowed_ids is not None:
        matches = [match for match in matches if match in allowed_ids]
    return matches[0] if len(matches) == 1 else None


def canonicalize_stage05_reread_invocation(stage: dict[str, Any]) -> None:
    entries = stage.get("per_burden_reread")
    if not isinstance(entries, list):
        return
    rewrites: list[dict[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("reread")
        if not isinstance(raw, str) or not raw.strip():
            continue
        canonical = STAGE05_REREAD_PREFIX_RE.sub("R(H,Δ): ", raw.strip(), count=1)
        if canonical == raw:
            continue
        entry["reread"] = canonical
        rewrites.append(
            {
                "burden_id": str(entry.get("burden_id") or ""),
                "raw_reread": raw,
                "canonical_reread": canonical,
            }
        )
    if rewrites:
        normalization = normalization_object(stage)
        normalization["per_burden_reread_rh_delta_canonicalizations"] = rewrites
        stage["normalization"] = normalization


def normalize_stage02_diagnostic_fields(stage: dict[str, Any]) -> None:
    normalization = normalization_object(stage)

    selected = stage.get("selected_n_frame")
    if isinstance(selected, dict):
        token = non_empty_string(selected.get("token") or selected.get("id") or selected.get("n_frame"))
        if token is None:
            raise HarnessError("stage-02 selected_n_frame object cannot be normalized without a string token")
        stage["selected_n_frame_details"] = selected
        stage["selected_n_frame"] = token
        normalization["selected_n_frame_from_details"] = True
    elif not isinstance(selected, str) or not selected.strip():
        raise HarnessError("stage-02 selected_n_frame must be a non-empty string token")

    floor = stage.get("burden_floor")
    if isinstance(floor, list) and floor and all(isinstance(item, str) and item for item in floor):
        canonical_floor: list[str] = []
        for index, item in enumerate(floor):
            raw = item.strip()
            if CANONICAL_BURDEN_ID_RE.fullmatch(raw) is None:
                raise HarnessError(
                    f"stage-02 burden_floor[{index}] must be a bare canonical burden id such as B1"
                )
            canonical_floor.append(raw)
        stage["burden_floor"] = ordered_unique(canonical_floor)
        detail_alias = stage.get("burden_floor_details")
        if detail_alias is None and isinstance(stage.get("burden_floor_detail"), list):
            detail_alias = stage.get("burden_floor_detail")
            stage["burden_floor_details"] = list(detail_alias)
            normalization["burden_floor_detail_alias"] = True
        if detail_alias is not None:
            if isinstance(detail_alias, dict):
                floor_ids = list(stage["burden_floor"])
                detail_keys = list(detail_alias.keys())
                canonical_keys: list[str] = []
                for key in detail_keys:
                    if not isinstance(key, str) or CANONICAL_BURDEN_ID_RE.fullmatch(key) is None:
                        raise HarnessError(
                            "stage-02 burden_floor_details keyed object keys must be canonical burden ids"
                        )
                    canonical_keys.append(key)
                if set(canonical_keys) != set(floor_ids):
                    raise HarnessError(
                        "stage-02 burden_floor_details keyed object keys must exactly match burden_floor"
                    )
                normalized_details: list[dict[str, Any]] = []
                for burden_id in floor_ids:
                    detail = detail_alias.get(burden_id)
                    if not isinstance(detail, dict):
                        raise HarnessError(
                            f"stage-02 burden_floor_details.{burden_id} must be an object"
                        )
                    raw_detail_id = detail.get("burden_id") or detail.get("id")
                    if raw_detail_id is not None and raw_detail_id != burden_id:
                        raise HarnessError(
                            f"stage-02 burden_floor_details.{burden_id} burden_id/id must match its key"
                        )
                    normalized_detail = dict(detail)
                    normalized_detail["burden_id"] = burden_id
                    normalized_details.append(normalized_detail)
                detail_alias = normalized_details
                stage["burden_floor_details"] = normalized_details
                normalization["burden_floor_details_keyed_map"] = True
            if not isinstance(detail_alias, list) or not all(isinstance(item, dict) for item in detail_alias):
                raise HarnessError("stage-02 burden_floor_details must be a list of detail objects")
            for index, detail in enumerate(detail_alias):
                burden_id = non_empty_string(detail.get("burden_id") or detail.get("id"))
                if burden_id is None:
                    raise HarnessError(
                        f"stage-02 burden_floor_details[{index}] object cannot be normalized without a string burden_id"
                    )
                if CANONICAL_BURDEN_ID_RE.fullmatch(burden_id) is None:
                    raise HarnessError(
                        f"stage-02 burden_floor_details[{index}].burden_id must be a canonical burden id"
                    )
                if burden_id not in stage["burden_floor"]:
                    raise HarnessError(
                        f"stage-02 burden_floor_details[{index}].burden_id must appear in burden_floor"
                    )
    elif isinstance(floor, list) and floor and all(isinstance(item, dict) for item in floor):
        details = list(floor)
        burden_ids: list[str] = []
        for index, detail in enumerate(details):
            burden_id = non_empty_string(detail.get("burden_id") or detail.get("id"))
            if burden_id is None:
                raise HarnessError(
                    f"stage-02 burden_floor[{index}] object cannot be normalized without a string burden_id"
                )
            burden_ids.append(burden_id)
        stage["burden_floor_details"] = details
        stage["burden_floor"] = ordered_unique(burden_ids)
        normalization["burden_floor_from_details"] = True
        normalization["canonical_burden_floor"] = list(stage["burden_floor"])
    else:
        raise HarnessError("stage-02 burden_floor must be a non-empty list of burden-id strings")

    registers = stage.get("live_registers")
    if isinstance(registers, list) and registers and all(isinstance(item, str) and item for item in registers):
        stage["live_registers"] = ordered_unique(list(registers))
    elif isinstance(registers, list) and registers and all(isinstance(item, dict) for item in registers):
        details = list(registers)
        register_ids: list[str] = []
        for index, detail in enumerate(details):
            register_id = non_empty_string(detail.get("id") or detail.get("register"))
            if register_id is None:
                raise HarnessError(
                    f"stage-02 live_registers[{index}] object cannot be normalized without a string id"
                )
            register_ids.append(register_id)
        stage["live_register_details"] = details
        stage["live_registers"] = ordered_unique(register_ids)
        normalization["live_registers_from_details"] = True
        normalization["canonical_live_registers"] = list(stage["live_registers"])
    else:
        raise HarnessError("stage-02 live_registers must be a non-empty list of register strings")

    if normalization:
        stage["normalization"] = normalization


def normalize_stage03_route_targets(stage: dict[str, Any]) -> None:
    route_targets = stage.get("route_targets")
    if isinstance(route_targets, list) and all(isinstance(item, str) and item for item in route_targets):
        stage["route_targets"] = ordered_unique(list(route_targets))
        return
    if isinstance(route_targets, list) and route_targets and all(isinstance(item, dict) for item in route_targets):
        details = list(route_targets)
        burden_ids: list[str] = []
        for index, detail in enumerate(details):
            burden_id = detail.get("burden_id")
            if not isinstance(burden_id, str) or not burden_id.strip():
                raise HarnessError(
                    f"stage-03 route_targets[{index}] object cannot be normalized without a string burden_id"
                )
            burden_ids.append(burden_id)
        stage["route_target_details"] = details
        stage["route_targets"] = ordered_unique(burden_ids)
        normalization = normalization_object(stage)
        normalization["route_targets_from_details"] = True
        normalization["canonical_route_targets"] = list(stage["route_targets"])
        stage["normalization"] = normalization
        return
    raise HarnessError("stage-03 route_targets must be a non-empty list of burden-id strings")


def canonicalize_stage03_owner_route_alias(
    route: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str] | None]:
    canonical = dict(route)
    raw_owner = non_empty_string(canonical.get("owner_id") or canonical.get("owner"))
    if raw_owner is None:
        return canonical, None
    operation = non_empty_string(canonical.get("operation") or canonical.get("owner_operation"))
    family, callable_owner = family_alias_execution_owner(raw_owner, operation)
    if not family or not callable_owner or " or " in callable_owner:
        return canonical, None
    canonical["owner_id"] = callable_owner
    if "owner" in canonical and "owner_id" not in route:
        canonical.pop("owner", None)
    canonical.setdefault("classification_family", family)
    return canonical, {
        "burden_id": str(canonical.get("burden_id") or canonical.get("target") or ""),
        "raw_owner_id": raw_owner,
        "canonical_owner_id": callable_owner,
        "classification_family": family,
    }


def canonicalize_stage03_owner_route_family_hint(
    route: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str] | None]:
    canonical = dict(route)
    raw_owner = non_empty_string(canonical.get("owner_id") or canonical.get("owner"))
    raw_family = non_empty_string(canonical.get("owner_family") or canonical.get("classification_family"))
    operation = non_empty_string(canonical.get("operation") or canonical.get("owner_operation"))
    if raw_owner is None or raw_family is None or operation is None:
        return canonical, None
    execution_owner = route_owner_family_hint_execution_owner(canonical)
    if not execution_owner:
        return canonical, None
    family = canonical_delta_owner(raw_family)
    canonical["owner_id"] = execution_owner
    if "owner" in canonical and "owner_id" not in route:
        canonical.pop("owner", None)
    if family:
        canonical.setdefault("classification_family", family)
    return canonical, {
        "burden_id": str(canonical.get("burden_id") or canonical.get("target") or ""),
        "raw_owner_id": raw_owner,
        "owner_family": raw_family,
        "canonical_owner_id": execution_owner,
        "operation": operation,
        "classification_family": family or raw_family,
    }


def canonicalize_stage03_owner_route_operation(
    route: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str] | None]:
    canonical = dict(route)
    owner = non_empty_string(canonical.get("owner_id") or canonical.get("owner"))
    operation = non_empty_string(canonical.get("operation") or canonical.get("owner_operation"))
    if owner is None or operation is None:
        return canonical, None
    family = canonical_delta_owner(owner)
    if family != "M9":
        return canonical, None
    canonical_operation = M9_RESULT_TOKEN_OPERATION_MAP.get(operation)
    if canonical_operation is None:
        return canonical, None
    canonical["operation"] = canonical_operation
    if "owner_operation" in canonical:
        canonical["owner_operation"] = canonical_operation
    return canonical, {
        "burden_id": str(canonical.get("burden_id") or canonical.get("target") or ""),
        "owner_id": owner,
        "raw_operation": operation,
        "canonical_operation": canonical_operation,
        "classification_family": family,
    }


def normalize_stage03_owner_routes(stage: dict[str, Any]) -> None:
    routes = stage.get("owner_routes")
    if isinstance(routes, list) and routes and all(isinstance(item, dict) for item in routes):
        canonical: list[dict[str, Any]] = []
        details: list[dict[str, Any]] = []
        alias_events: list[dict[str, str]] = []
        family_hint_events: list[dict[str, str]] = []
        operation_events: list[dict[str, str]] = []
        for index, route in enumerate(routes):
            burden_id = non_empty_string(route.get("burden_id"))
            owner_id = non_empty_string(route.get("owner_id"))
            if burden_id is not None and owner_id is not None:
                canonical_row, family_hint_event = canonicalize_stage03_owner_route_family_hint(route)
                if family_hint_event is not None:
                    family_hint_events.append(family_hint_event)
                route = canonical_row
                canonical_row, alias_event = canonicalize_stage03_owner_route_alias(route)
                if alias_event is not None:
                    alias_events.append(alias_event)
                canonical_row, operation_event = canonicalize_stage03_owner_route_operation(canonical_row)
                if operation_event is not None:
                    operation_events.append(operation_event)
                route_errors = route_owner_vocabulary_errors(f"stage-03 owner_routes[{index}]", canonical_row)
                if route_errors:
                    raise HarnessError(route_errors[0])
                canonical.append(canonical_row)
                continue

            target = non_empty_string(route.get("target") or route.get("burden_id"))
            required = route.get("required")
            if target is None or not isinstance(required, list) or not required:
                raise HarnessError(
                    f"stage-03 owner_routes[{index}] must carry burden_id/owner_id or target plus required owner rows"
                )
            details.append(route)
            for required_index, required_row in enumerate(required):
                if not isinstance(required_row, dict):
                    raise HarnessError(
                        f"stage-03 owner_routes[{index}].required[{required_index}] must be an object"
                    )
                owner = non_empty_string(required_row.get("owner_id") or required_row.get("owner"))
                if owner is None:
                    raise HarnessError(
                        f"stage-03 owner_routes[{index}].required[{required_index}] cannot be normalized without owner"
                    )
                canonical_row: dict[str, Any] = {
                    "burden_id": target,
                    "owner_id": owner,
                }
                operation = non_empty_string(required_row.get("operation") or required_row.get("owner_operation"))
                if operation is not None:
                    canonical_row["operation"] = operation
                eligibility = non_empty_string(route.get("classification") or route.get("policy_id"))
                if eligibility is not None:
                    canonical_row["eligibility"] = eligibility
                raw_family = non_empty_string(required_row.get("owner_family") or required_row.get("classification_family"))
                if raw_family is not None:
                    canonical_row["owner_family"] = raw_family
                canonical_row, family_hint_event = canonicalize_stage03_owner_route_family_hint(canonical_row)
                if family_hint_event is not None:
                    family_hint_events.append(family_hint_event)
                canonical_row, alias_event = canonicalize_stage03_owner_route_alias(canonical_row)
                if alias_event is not None:
                    alias_events.append(alias_event)
                canonical_row, operation_event = canonicalize_stage03_owner_route_operation(canonical_row)
                if operation_event is not None:
                    operation_events.append(operation_event)
                route_errors = route_owner_vocabulary_errors(
                    f"stage-03 owner_routes[{index}].required[{required_index}]",
                    canonical_row,
                )
                if route_errors:
                    raise HarnessError(route_errors[0])
                canonical.append(canonical_row)

        if not canonical:
            raise HarnessError("stage-03 owner_routes must name at least one owner route")
        stage["owner_routes"] = canonical
        if details or alias_events or family_hint_events or operation_events:
            stage["owner_route_details"] = details
            normalization = normalization_object(stage)
            if details:
                normalization["owner_routes_from_required_details"] = True
            if alias_events:
                normalization["owner_route_family_aliases"] = alias_events
            if family_hint_events:
                normalization["owner_route_family_hints"] = family_hint_events
            if operation_events:
                normalization["owner_route_operation_result_tokens"] = operation_events
            normalization["canonical_owner_routes"] = [
                {"burden_id": row.get("burden_id"), "owner_id": row.get("owner_id")} for row in canonical
            ]
            stage["normalization"] = normalization
        return
    raise HarnessError("stage-03 owner_routes must be a non-empty list of owner-route objects")


def extract_stage04_body_ref(act_row: str) -> str | None:
    match = ACT_BODY_REF_RE.search(act_row)
    return match.group(1) if match else None


def normalize_string_list(stage: dict[str, Any], key: str, *, required: bool) -> list[str]:
    value = stage.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise HarnessError(f"stage-04 {key} must be a string list")
    normalized = ordered_unique(list(value))
    stage[key] = normalized
    return normalized


def normalize_stage04_burden_ids(
    stage: dict[str, Any],
    key: str,
    *,
    allowed_ids: set[str],
    normalization: dict[str, Any],
) -> list[str]:
    value = stage.get(key)
    if not isinstance(value, list) or not value:
        raise HarnessError(f"stage-04 {key} must be a non-empty burden-id list")

    canonical: list[str] = []
    details: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, str) and item.strip():
            burden_id = canonical_burden_id_from_text(item, allowed_ids)
            if burden_id is None:
                raise HarnessError(f"stage-04 {key}[{index}] cannot be normalized to a routed burden id")
            canonical.append(burden_id)
            if item.strip() != burden_id:
                details.append({"raw": item, "burden_id": burden_id})
        elif isinstance(item, dict):
            burden_id = non_empty_string(item.get("burden_id") or item.get("id"))
            if burden_id is None:
                raise HarnessError(f"stage-04 {key}[{index}] object cannot be normalized without a string burden_id")
            burden_id = burden_id.strip()
            if burden_id not in allowed_ids:
                raise HarnessError(f"stage-04 {key}[{index}] burden_id is not routed: {burden_id}")
            canonical.append(burden_id)
            details.append(dict(item))
        else:
            raise HarnessError(f"stage-04 {key} must contain burden-id strings or burden objects")

    stage[key] = ordered_unique(canonical)
    if details:
        stage[f"{key}_details"] = details
        normalization[f"{key}_normalized_to_canonical_ids"] = True
        normalization[f"canonical_{key}"] = list(stage[key])
    return stage[key]


def parsed_stage04_act_detail(row: str) -> dict[str, str] | None:
    match = ACT_ROW_DETAIL_RE.match(row)
    if not match:
        return None
    body_ref = match.group("body_ref")
    if body_ref != match.group("body_ref_field"):
        return None
    return {
        "act_row": row,
        "body_ref": body_ref,
        "burden_id": burden_id_from_land(match.group("land")),
        "owner_id": match.group("owner"),
        "operation": match.group("operation"),
        "pressure": match.group("pressure").strip(),
        "delta": match.group("delta"),
        "delta_result": match.group("delta_result").strip(),
        "land": match.group("land"),
    }


def parsed_stage04_act_rows(stage: dict[str, Any]) -> list[dict[str, str]]:
    parsed_rows: list[dict[str, str]] = []
    for index, row in enumerate(stage.get("act_rows", [])):
        parsed = parsed_stage04_act_detail(row)
        if not parsed:
            raise HarnessError(f"stage-04 act_rows[{index}] is not a parseable canonical ACT row")
        encoded_burden = body_ref_burden_id(parsed["body_ref"])
        if encoded_burden and parsed["burden_id"] and encoded_burden != parsed["burden_id"]:
            raise HarnessError(
                f"stage-04 act_rows[{index}] body_ref {parsed['body_ref']!r} encodes "
                f"{encoded_burden} but Land() targets {parsed['burden_id']}"
            )
        parsed_rows.append(parsed)
    return parsed_rows


def reject_stage04_body_ref_token(raw_body_ref: str) -> None:
    if "[" in raw_body_ref or "]" in raw_body_ref:
        raise HarnessError(
            "stage-04 body_ref must be the bare burden/submove join key; "
            "owner.operation belongs in owner_id/operation fields"
        )


def normalize_stage04_act_row_details(
    stage: dict[str, Any],
    *,
    act_targets: list[str],
    act_burdens: list[str],
    normalization: dict[str, Any],
) -> None:
    raw_details = stage.get("act_row_details")
    if raw_details is None:
        raise HarnessError("stage-04 act_row_details is required to carry typed owner/operation/register_axis evidence")
    if not isinstance(raw_details, list):
        raise HarnessError("stage-04 act_row_details must be a list when present")

    parsed_by_ref: dict[str, dict[str, str]] = {}
    parsed_by_row: dict[str, dict[str, str]] = {}
    for row in stage.get("act_rows", []):
        parsed = parsed_stage04_act_detail(row)
        if not parsed:
            continue
        parsed_by_ref[parsed["body_ref"]] = parsed
        parsed_by_row[row] = parsed

    allowed_burdens = set(act_targets) | set(act_burdens)
    normalized: list[dict[str, Any]] = []
    hydrated: list[dict[str, str]] = []
    for index, detail in enumerate(raw_details):
        if not isinstance(detail, dict):
            raise HarnessError(f"stage-04 act_row_details[{index}] must be an object")

        raw_act_row = non_empty_string(detail.get("act_row"))
        raw_body_ref = non_empty_string(detail.get("body_ref"))
        canonical_raw_act_row = None
        if raw_act_row:
            canonical_raw_act_row, raw_act_rewrite = canonicalize_stage04_act_row(raw_act_row)
            if raw_act_rewrite:
                normalization.setdefault("act_row_details_act_row_canonicalizations", []).append(raw_act_rewrite)
        parsed = parsed_by_row.get(canonical_raw_act_row or raw_act_row or "")
        if parsed is None and raw_act_row:
            parsed_from_raw = parsed_stage04_act_detail(canonical_raw_act_row or raw_act_row)
            if parsed_from_raw:
                parsed = parsed_by_ref.get(parsed_from_raw["body_ref"])
        canonical_raw_body_ref = raw_body_ref
        if raw_body_ref:
            reject_stage04_body_ref_token(raw_body_ref)
        if parsed is None and canonical_raw_body_ref:
            parsed = parsed_by_ref.get(canonical_raw_body_ref)
        if parsed is None:
            raise HarnessError(
                f"stage-04 act_row_details[{index}] cannot be normalized without "
                "a parseable act_row or body_ref tied to Stage 04 act_rows"
            )

        item = dict(detail)
        missing: list[str] = []
        if canonical_raw_body_ref and canonical_raw_body_ref != parsed["body_ref"]:
            raise HarnessError(
                f"stage-04 act_row_details[{index}].body_ref disagrees with parsed ACT row body_ref"
            )
        if raw_body_ref and canonical_raw_body_ref != raw_body_ref:
            item["body_ref"] = canonical_raw_body_ref
            missing.append("body_ref")
        elif not raw_body_ref:
            item["body_ref"] = parsed["body_ref"]
            missing.append("body_ref")

        raw_burden = non_empty_string(item.get("burden_id") or item.get("id") or item.get("target"))
        parsed_burden = parsed["burden_id"]
        if raw_burden:
            canonical = canonical_burden_id_from_text(raw_burden, allowed_burdens or None)
            if canonical is None:
                raise HarnessError(f"stage-04 act_row_details[{index}].burden_id is not canonicalizable")
            if parsed_burden and canonical != parsed_burden:
                raise HarnessError(
                    f"stage-04 act_row_details[{index}].burden_id disagrees with parsed ACT row Land()"
                )
            item["burden_id"] = canonical
        else:
            if not parsed_burden:
                raise HarnessError(f"stage-04 act_row_details[{index}] cannot derive burden_id from ACT row")
            item["burden_id"] = parsed_burden
            missing.append("burden_id")

        for field in ("owner_id", "operation", "act_row"):
            value = non_empty_string(item.get(field))
            parsed_value = parsed[field]
            if field == "operation" and value and value != parsed_value:
                canonical_value = canonicalize_stage04_operation_token(
                    parsed["owner_id"],
                    value,
                    item.get("pressure") or parsed["pressure"],
                    item.get("delta_result") or parsed["delta_result"],
                )
                if canonical_value == parsed_value:
                    item[field] = parsed_value
                    missing.append(field)
                    continue
            if value and field != "act_row" and value != parsed_value:
                raise HarnessError(f"stage-04 act_row_details[{index}].{field} disagrees with parsed ACT row")
            if not value or (field == "act_row" and value != parsed_value):
                item[field] = parsed_value
                missing.append(field)

        detail_delta_result = non_empty_string(item.get("delta_result"))
        if not detail_delta_result:
            raise HarnessError(f"stage-04 act_row_details[{index}].delta_result is required")
        detail_delta_result = canonical_delta_result_for_owner(
            parsed["owner_id"],
            parsed["operation"],
            item.get("pressure") or parsed["pressure"],
            detail_delta_result,
        )
        if item.get("delta_result") != detail_delta_result:
            item["delta_result"] = detail_delta_result
            missing.append("delta_result")
        require_delta_result_vocabulary(
            f"stage-04 act_row_details[{index}].delta_result",
            parsed["owner_id"],
            detail_delta_result,
        )
        pressure_errors = source_pressure_delta_errors(
            f"stage-04 act_row_details[{index}].delta_result",
            parsed["owner_id"],
            item.get("pressure") or parsed["pressure"],
            detail_delta_result,
        )
        if pressure_errors:
            raise HarnessError("; ".join(pressure_errors))
        operation_delta_errors = owner_operation_delta_result_errors(
            f"stage-04 act_row_details[{index}].delta_result",
            parsed["owner_id"],
            parsed["operation"],
            detail_delta_result,
        )
        if operation_delta_errors:
            raise HarnessError("; ".join(operation_delta_errors))
        if detail_delta_result != parsed["delta_result"]:
            raise HarnessError(
                f"stage-04 act_row_details[{index}].delta_result disagrees with parsed ACT row"
            )

        register_axis, axis_rewritten = require_stage04_register_axis(
            index=index,
            item=item,
            parsed=parsed,
        )
        if item.get("register_axis") != register_axis:
            item["register_axis"] = register_axis
            missing.append("register_axis")
        if "axis" in item and item.get("axis") != register_axis:
            item["axis"] = register_axis
            if not axis_rewritten:
                missing.append("axis")

        normalized.append(item)
        if missing:
            hydrated.append({"body_ref": parsed["body_ref"], "fields": ",".join(ordered_unique(missing))})

    stage["act_row_details"] = normalized
    if hydrated:
        normalization["act_row_details_hydrated_from_act_rows"] = hydrated


def normalize_stage04_act_fields(stage: dict[str, Any]) -> None:
    act_targets = normalize_string_list(stage, "act_targets", required=True)
    normalization = normalization_object(stage)
    act_burdens = normalize_stage04_burden_ids(
        stage,
        "act_burdens",
        allowed_ids=set(act_targets),
        normalization=normalization,
    )
    raw_rows = stage.get("act_rows")

    if isinstance(raw_rows, list) and raw_rows and all(isinstance(item, str) and item for item in raw_rows):
        act_rows, row_rewrites = canonicalize_stage04_act_rows(ordered_unique(list(raw_rows)))
        stage["act_rows"] = act_rows
    elif isinstance(raw_rows, list) and raw_rows and all(isinstance(item, dict) for item in raw_rows):
        details = list(raw_rows)
        act_rows = []
        for index, detail in enumerate(details):
            act_row = detail.get("act_row")
            if not isinstance(act_row, str) or not act_row.strip():
                raise HarnessError(
                    f"stage-04 act_rows[{index}] object cannot be normalized without a string act_row"
                )
            act_rows.append(act_row)
        stage["act_row_details"] = details
        act_rows, row_rewrites = canonicalize_stage04_act_rows(ordered_unique(act_rows))
        stage["act_rows"] = act_rows
        normalization["act_rows_from_details"] = True
        normalization["canonical_act_rows"] = list(stage["act_rows"])
    else:
        raise HarnessError("stage-04 act_rows must be a non-empty list of ACT row strings")
    record_stage04_act_row_canonicalizations(normalization, row_rewrites)

    parsed_rows = parsed_stage04_act_rows(stage)
    row_body_refs = ordered_unique([item["body_ref"] for item in parsed_rows])

    explicit_body_refs = stage.get("act_body_refs")
    if explicit_body_refs is None or explicit_body_refs == []:
        if not row_body_refs:
            raise HarnessError("stage-04 act_body_refs missing and no body_ref tokens were extractable from ACT rows")
        stage["act_body_refs"] = row_body_refs
        normalization["act_body_refs_from_act_rows"] = True
    else:
        explicit_refs = normalize_string_list(stage, "act_body_refs", required=True)
        normalized_refs: list[str] = []
        for index, raw_ref in enumerate(explicit_refs):
            reject_stage04_body_ref_token(raw_ref)
            if raw_ref not in row_body_refs:
                raise HarnessError(f"stage-04 act_body_refs[{index}] is not tied to a canonical ACT row body_ref")
            normalized_refs.append(raw_ref)
        normalized_refs = ordered_unique(normalized_refs)
        if normalized_refs != row_body_refs:
            raise HarnessError("stage-04 act_body_refs must match canonical ACT row body_refs in row order")
        stage["act_body_refs"] = normalized_refs

    normalize_stage04_act_row_details(
        stage,
        act_targets=act_targets,
        act_burdens=act_burdens,
        normalization=normalization,
    )

    if normalization:
        stage["normalization"] = normalization


def normalize_stage05_mrp_fields(stage: dict[str, Any]) -> None:
    terminal_states = stage.get("terminal_states")
    if not isinstance(terminal_states, dict) or not terminal_states:
        raise HarnessError("stage-05 terminal_states must be a non-empty object")
    if not all(isinstance(key, str) and key and isinstance(value, str) and value for key, value in terminal_states.items()):
        raise HarnessError("stage-05 terminal_states must map burden-id strings to terminal-state strings")
    for burden_id, terminal_state in terminal_states.items():
        if not STAGE05_TERMINAL_BURDEN_ID_RE.fullmatch(burden_id):
            raise HarnessError(
                "stage-05 terminal_states keys must be canonical burden ids such as B1; "
                f"got {burden_id!r}"
            )
        state = terminal_state.strip()
        if state != terminal_state:
            terminal_states[burden_id] = state
        if state not in CONTROLLED_STAGE05_TERMINAL_STATES:
            allowed = ", ".join(sorted(CONTROLLED_STAGE05_TERMINAL_STATES))
            raise HarnessError(
                "stage-05 terminal_states must use controlled terminal-state heads only "
                f"({allowed}); got {burden_id}={terminal_state!r}. Put delta/result detail "
                "in ACT/NAR/witness detail fields, not in terminal_states."
            )

    details = stage.get("terminal_state_details")
    if details is not None:
        if not isinstance(details, list):
            raise HarnessError("stage-05 terminal_state_details must be a list when present")
        for index, detail in enumerate(details):
            if not isinstance(detail, dict):
                raise HarnessError(f"stage-05 terminal_state_details[{index}] must be an object")
            burden_id = detail.get("burden_id")
            if not isinstance(burden_id, str) or burden_id not in terminal_states:
                raise HarnessError(
                    f"stage-05 terminal_state_details[{index}].burden_id must name a terminal burden"
                )
            state = detail.get("state")
            terminal_state = detail.get("terminal_state")
            if state is None and terminal_state is not None:
                state = terminal_state
                detail["state"] = terminal_state
            elif terminal_state is not None and state != terminal_state:
                raise HarnessError(
                    f"stage-05 terminal_state_details[{index}].state and .terminal_state must match"
                )
            if not isinstance(state, str) or state not in CONTROLLED_STAGE05_TERMINAL_STATES:
                raise HarnessError(
                    f"stage-05 terminal_state_details[{index}].state must use a controlled terminal state"
                )
            if terminal_states.get(burden_id) != state:
                raise HarnessError(
                    f"stage-05 terminal_state_details[{index}].state must match terminal_states"
                )
            basis = detail.get("basis")
            normalized_basis, basis_error = normalize_terminal_detail_basis(basis)
            if basis_error:
                raise HarnessError(f"stage-05 terminal_state_details[{index}].basis {basis_error}")
            if basis is not None:
                detail["basis"] = normalized_basis

    edges = stage.get("dependency_graph_edges")
    if edges is None:
        graph = stage.get("dependency_graph")
        if isinstance(graph, dict) and isinstance(graph.get("edges"), list):
            stage["dependency_graph_edges"] = graph["edges"]
        else:
            raise HarnessError("stage-05 dependency_graph_edges must be a list")
    elif not isinstance(edges, list):
        raise HarnessError("stage-05 dependency_graph_edges must be a list")

    if "no_new_resultant_proof" not in stage:
        raise HarnessError("stage-05 no_new_resultant_proof is required")
    proof = stage.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        if not isinstance(proof.get("proved"), bool):
            raise HarnessError("stage-05 no_new_resultant_proof.proved must be boolean")
        if proof.get("proved") is True and not str(proof.get("basis") or "").strip():
            raise HarnessError("stage-05 no_new_resultant_proof.basis is required when proved=true")
    elif not isinstance(proof, bool):
        raise HarnessError("stage-05 no_new_resultant_proof must be boolean or object")

    canonicalize_stage05_reread_invocation(stage)
    normalize_stage05_stage_level_pressure_activations(stage)
    normalize_stage05_negative_non_edge_public_burden_references(stage)
    normalize_stage05_held_route_gradient_identity(stage)
    normalize_stage05_per_burden_extra_fields(stage)
    per_burden_errors = staged_output.per_burden_reread_entry_errors(
        stage.get("per_burden_reread"),
        label="stage-05 per_burden_reread",
        terminal_state_ids=set(terminal_states),
    )
    if per_burden_errors:
        raise HarnessError(
            "stage-05 per_burden_reread is required: one honest reread record per terminal "
            "burden; Stage 07 renders the visible [Mid-Reread Pressure] blocks from these "
            "records and never fills missing fields. Problems:\n- " + "\n- ".join(per_burden_errors)
        )


def normalize_stage05_stage_level_pressure_activations(stage: dict[str, Any]) -> None:
    entries = stage.get("per_burden_reread")
    top_level = stage.get("pressure_activations")
    if not isinstance(entries, list) or not entries or not isinstance(top_level, dict):
        return
    if any(not isinstance(entry, dict) for entry in entries):
        return
    if any("pressure_activations" in entry for entry in entries):
        return
    if set(top_level) != staged_output.PER_BURDEN_PRESSURE_KEYS:
        return
    if not all(isinstance(value, str) and value.strip() for value in top_level.values()):
        return
    hydrated: list[str] = []
    for entry in entries:
        entry["pressure_activations"] = copy.deepcopy(top_level)
        burden = str(entry.get("burden_id") or "").strip()
        hydrated.append(burden or "<unknown>")
    normalization = normalization_object(stage)
    normalization["per_burden_pressure_activations_from_stage_level"] = hydrated
    stage["normalization"] = normalization


def stage05_known_burden_ids(stage: dict[str, Any]) -> set[str]:
    known: set[str] = set()
    for key in ("terminal_states",):
        value = stage.get(key)
        if isinstance(value, dict):
            known.update(b_id(raw) for raw in value.keys())
    for key in ("B_LA", "B_total", "nodes"):
        value = stage.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict):
                known.add(b_id(item.get("burden_id") or item.get("id") or item.get("target")))
            else:
                known.add(b_id(item))
    generated = stage.get("generated_burdens")
    if isinstance(generated, list):
        for item in generated:
            if isinstance(item, dict):
                known.add(b_id(item.get("burden_id") or item.get("id") or item.get("target")))
            else:
                known.add(b_id(item))
    entries = stage.get("per_burden_reread")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                known.add(b_id(entry.get("burden_id")))
    return {burden for burden in known if burden}


def normalize_negative_non_edge_public_text(
    value: str,
    *,
    known_burdens: set[str],
) -> tuple[str, list[dict[str, str]]]:
    text = str(value or "")
    if not NEGATIVE_NON_EDGE_REFERENCE_RE.search(text):
        return text, []
    rewrites: list[dict[str, str]] = []

    def replace_edge(match: re.Match[str]) -> str:
        source = canonical_burden_id(match.group("source"))
        target = canonical_burden_id(match.group("target"))
        if not target or target in known_burdens:
            return match.group(0)
        rewrites.append(
            {
                "raw_edge": match.group(0),
                "source_burden": source,
                "unknown_target_burden": target,
                "canonical_text": "an extra downstream edge",
            }
        )
        return "an extra downstream edge"

    normalized = PUBLIC_ASCII_EDGE_REFERENCE_RE.sub(replace_edge, text)
    normalized = PUBLIC_SUP_EDGE_REFERENCE_RE.sub(replace_edge, normalized)
    return normalized, rewrites


def normalize_stage05_negative_non_edge_public_burden_references(stage: dict[str, Any]) -> None:
    known_burdens = stage05_known_burden_ids(stage)
    if not known_burdens:
        return
    rewrites: list[dict[str, str]] = []

    def normalize_activation_map(
        activations: Any,
        *,
        burden_id: str,
        field_prefix: str,
    ) -> None:
        if not isinstance(activations, dict):
            return
        for key, raw in list(activations.items()):
            if not isinstance(raw, str):
                continue
            normalized, field_rewrites = normalize_negative_non_edge_public_text(
                raw,
                known_burdens=known_burdens,
            )
            if not field_rewrites:
                continue
            activations[key] = normalized
            for event in field_rewrites:
                rewrites.append(
                    {
                        "burden_id": burden_id,
                        "field": f"{field_prefix}.{key}",
                        **event,
                    }
                )

    normalize_activation_map(
        stage.get("pressure_activations"),
        burden_id="<stage>",
        field_prefix="pressure_activations",
    )
    entries = stage.get("per_burden_reread")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalize_activation_map(
                entry.get("pressure_activations"),
                burden_id=str(entry.get("burden_id") or ""),
                field_prefix="pressure_activations",
            )
    if rewrites:
        normalization = normalization_object(stage)
        normalization["negative_non_edge_public_burden_references"] = rewrites
        stage["normalization"] = normalization


def stage05_route_gradient_has_held_identity(gradient: str, target: str) -> bool:
    if has_raw_machine_burden(gradient, target) or public_burden_id(target) in gradient:
        return True
    if re.search(r"(?i)\b(?:held|initial|already[- ]inventoried|already named)\b", gradient):
        return True
    if re.search(r"(?:B[1-9][0-9]*|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s*(?:->|→)\s*(?:B[1-9][0-9]*|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)", gradient):
        return True
    return False


def normalize_stage05_held_route_gradient_identity(stage: dict[str, Any]) -> None:
    entries = stage.get("per_burden_reread")
    if not isinstance(entries, list):
        return
    rewrites: list[dict[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        route_type = str(entry.get("route_result_type") or "").strip()
        if route_type != "held_burden_activation":
            continue
        target = stage07_route_target_from_graph(entry.get("graph_delta"))
        if not target:
            continue
        gradient = str(entry.get("route_gradient") or "")
        if not gradient.strip() or stage05_route_gradient_has_held_identity(gradient, target):
            continue
        canonical = gradient.rstrip(". ") + f". already-held {target} from B_LA."
        entry["route_gradient"] = canonical
        rewrites.append(
            {
                "source_burden": str(entry.get("burden_id") or ""),
                "target_burden": target,
                "canonical_route_gradient": canonical,
            }
        )
    if rewrites:
        normalization = normalization_object(stage)
        normalization["held_route_gradient_identity"] = rewrites
        stage["normalization"] = normalization


def normalize_stage05_per_burden_extra_fields(stage: dict[str, Any]) -> None:
    entries = stage.get("per_burden_reread")
    if not isinstance(entries, list):
        return
    stripped: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or "no_new_resultant_proof" not in entry:
            continue
        route_type = str(entry.get("route_result_type") or "").strip()
        route = str(entry.get("route") or "").strip().upper()
        if route_type == "no_new_resultant" and route == "STOP":
            entry.pop("no_new_resultant_proof", None)
            burden = str(entry.get("burden_id") or "").strip()
            stripped.append(burden or "<unknown>")
    if stripped:
        normalization = normalization_object(stage)
        normalization["stripped_per_burden_no_new_resultant_proof"] = stripped
        stage["normalization"] = normalization


def normalize_stage06_register_delta_value(
    value: Any,
    *,
    empty_string_message: str,
    list_message: str,
    type_message: str,
) -> str | list[str]:
    if isinstance(value, str):
        if not value:
            raise HarnessError(empty_string_message)
        return value
    if isinstance(value, list):
        if not value or not all(isinstance(item, str) and item for item in value):
            raise HarnessError(list_message)
        return ordered_unique(list(value))
    raise HarnessError(type_message)


def normalize_stage06_witness_nar_fields(stage: dict[str, Any]) -> None:
    field_refs = stage.get("field_witness_body_refs")
    if not isinstance(field_refs, list) or not field_refs or not all(isinstance(item, str) and item for item in field_refs):
        raise HarnessError("stage-06 field_witness_body_refs must be a non-empty string list")
    stage["field_witness_body_refs"] = ordered_unique(list(field_refs))

    nar_burdens = stage.get("nar_burdens")
    if not isinstance(nar_burdens, list) or not nar_burdens or not all(isinstance(item, str) and item for item in nar_burdens):
        raise HarnessError("stage-06 nar_burdens must be a non-empty string list")
    stage["nar_burdens"] = ordered_unique(list(nar_burdens))

    owner_activations = stage.get("owner_activations")
    if isinstance(owner_activations, list) and owner_activations and all(isinstance(item, str) and item for item in owner_activations):
        stage["owner_activations"] = ordered_unique(list(owner_activations))
    elif isinstance(owner_activations, list) and owner_activations and all(isinstance(item, dict) for item in owner_activations):
        details = []
        delta_rewrites: list[dict[str, str]] = []
        for raw_detail in owner_activations:
            detail, rewrite = canonicalize_delta_fields(dict(raw_detail))
            details.append(detail)
            if rewrite:
                delta_rewrites.append(rewrite)
        refs: list[str] = []
        for index, detail in enumerate(details):
            body_ref = detail.get("body_ref")
            if not isinstance(body_ref, str) or not body_ref:
                raise HarnessError(f"stage-06 owner_activations[{index}] object cannot be normalized without body_ref")
            refs.append(body_ref)
        stage["owner_activation_details"] = details
        stage["owner_activations"] = ordered_unique(refs)
        normalization = stage.get("normalization")
        if not isinstance(normalization, dict):
            normalization = {}
        normalization["owner_activations_from_details"] = True
        normalization["canonical_owner_activations"] = list(stage["owner_activations"])
        if delta_rewrites:
            normalization["owner_activation_delta_result_canonicalizations"] = delta_rewrites
        stage["normalization"] = normalization
    else:
        raise HarnessError("stage-06 owner_activations must be body-ref strings or objects with body_ref")

    if "normalized_activation_record" not in stage:
        raise HarnessError("stage-06 normalized_activation_record is required")
    normalized = stage.get("normalized_activation_record")
    if isinstance(normalized, bool):
        if normalized is not True:
            raise HarnessError("stage-06 normalized_activation_record boolean must be true")
    elif isinstance(normalized, dict):
        normalize_stage06_nar_object(normalized, "stage-06 normalized_activation_record")
    else:
        raise HarnessError("stage-06 normalized_activation_record must be true or an object")
    details = stage.get("normalized_activation_record_details")
    if details is not None:
        hydrate_stage06_nar_details(details, normalized)
        normalize_stage06_nar_object(details, "stage-06 normalized_activation_record_details")

    if "register_deltas" not in stage:
        if isinstance(normalized, dict) and "register_deltas" in normalized:
            raise HarnessError(
                "stage-06 register_deltas is required at top level; "
                "normalized_activation_record.register_deltas is mirror evidence only"
            )
        raise HarnessError("stage-06 register_deltas is required")
    register_deltas = stage.get("register_deltas")
    if isinstance(register_deltas, dict):
        for register, delta in register_deltas.items():
            if not isinstance(register, str) or not register:
                raise HarnessError("stage-06 register_deltas keys must be non-empty strings")
            register_deltas[register] = normalize_stage06_register_delta_value(
                delta,
                empty_string_message="stage-06 register_deltas string values must be non-empty",
                list_message="stage-06 register_deltas list values must be non-empty strings",
                type_message="stage-06 register_deltas object values must be strings or string lists",
            )
    elif isinstance(register_deltas, list):
        for index, item in enumerate(register_deltas):
            if not isinstance(item, dict):
                raise HarnessError(f"stage-06 register_deltas[{index}] must be an object")
            if not isinstance(item.get("register"), str) or not item["register"]:
                raise HarnessError(f"stage-06 register_deltas[{index}].register must be a non-empty string")
            item["delta"] = normalize_stage06_register_delta_value(
                item.get("delta"),
                empty_string_message=f"stage-06 register_deltas[{index}].delta must be a non-empty string",
                list_message=f"stage-06 register_deltas[{index}].delta list values must be non-empty strings",
                type_message=(
                    f"stage-06 register_deltas[{index}].delta must be a non-empty string "
                    "or non-empty string list"
                ),
            )
    else:
        raise HarnessError("stage-06 register_deltas must be an object or list")


def normalize_stage06_nar_object(value: dict[str, Any], label: str) -> None:
    raw_n_frame = value.get("n_frame")
    if isinstance(raw_n_frame, dict):
        selected = raw_n_frame.get("selected")
        if not isinstance(selected, str) or not selected.strip():
            raise HarnessError(f"{label}.n_frame object cannot be normalized without a non-empty string selected token")
        if "n_frame_details" not in value:
            value["n_frame_details"] = dict(raw_n_frame)
        value["n_frame"] = selected.strip()
        normalization = value.get("normalization")
        if normalization is None:
            normalization = {}
        if not isinstance(normalization, dict):
            raise HarnessError(f"{label}.normalization must be an object when present")
        normalization["n_frame_from_selected_detail"] = True
        normalization["canonical_n_frame"] = value["n_frame"]
        value["normalization"] = normalization
    elif isinstance(raw_n_frame, str) and raw_n_frame.strip():
        value["n_frame"] = raw_n_frame.strip()
    else:
        raise HarnessError(f"{label}.n_frame must be a non-empty string")
    n_frame = value["n_frame"]
    n_frame_details = value.get("n_frame_details")
    if n_frame_details is not None:
        if not isinstance(n_frame_details, dict):
            raise HarnessError(f"{label}.n_frame_details must be an object when present")
        detail_selected = n_frame_details.get("selected")
        if detail_selected is not None:
            if not isinstance(detail_selected, str) or not detail_selected.strip():
                raise HarnessError(f"{label}.n_frame_details.selected must be a non-empty string when present")
            if detail_selected.strip() != n_frame:
                raise HarnessError(f"{label}.n_frame_details.selected must match canonical n_frame")
        detail_held = n_frame_details.get("held")
        held_tokens: set[str] = set()
        if detail_held is not None:
            if not isinstance(detail_held, list) or not all(isinstance(item, str) and item for item in detail_held):
                raise HarnessError(f"{label}.n_frame_details.held must be a string list when present")
            held_tokens = {item.strip() for item in detail_held}
        detail_held_details = n_frame_details.get("held_details")
        if detail_held_details is not None:
            if not isinstance(detail_held_details, list):
                raise HarnessError(f"{label}.n_frame_details.held_details must be an object list when present")
            for index, item in enumerate(detail_held_details):
                if not isinstance(item, dict):
                    raise HarnessError(f"{label}.n_frame_details.held_details[{index}] must be an object")
                detail_frame = non_empty_string(item.get("n_frame"))
                if detail_frame is None:
                    raise HarnessError(f"{label}.n_frame_details.held_details[{index}].n_frame must be a non-empty string")
                item["n_frame"] = detail_frame.strip()
                if held_tokens and item["n_frame"] not in held_tokens:
                    raise HarnessError(
                        f"{label}.n_frame_details.held_details[{index}].n_frame must appear in n_frame_details.held"
                    )
                detail_reason = non_empty_string(item.get("hold_reason"))
                if detail_reason is None:
                    raise HarnessError(
                        f"{label}.n_frame_details.held_details[{index}].hold_reason must be a non-empty string"
                    )
                item["hold_reason"] = detail_reason.strip()
    normalization = value.get("normalization")
    if normalization is not None and not isinstance(normalization, dict):
        raise HarnessError(f"{label}.normalization must be an object when present")
    for key in ("live_registers", "burden_floor"):
        raw = value.get(key)
        if not isinstance(raw, list) or not all(isinstance(item, str) and item for item in raw):
            raise HarnessError(f"{label}.{key} must be a string list")
        value[key] = ordered_unique(list(raw))
    rows = value.get("per_burden")
    if isinstance(rows, dict) and rows:
        normalized_rows: list[dict[str, Any]] = []
        for raw_burden_id, payload in rows.items():
            if not isinstance(raw_burden_id, str) or not raw_burden_id:
                raise HarnessError(f"{label}.per_burden map keys must be non-empty burden ids")
            if not isinstance(payload, dict):
                raise HarnessError(f"{label}.per_burden[{raw_burden_id}] must be an object")
            row = dict(payload)
            row.setdefault("burden_id", raw_burden_id)
            normalized_rows.append(row)
        rows = normalized_rows
        value["per_burden"] = rows
    if not isinstance(rows, list) or not rows:
        raise HarnessError(f"{label}.per_burden must be a non-empty object list")
    delta_rewrites: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HarnessError(f"{label}.per_burden[{index}] must be an object")
        if not isinstance(row.get("burden_id"), str) or not row["burden_id"]:
            raise HarnessError(f"{label}.per_burden[{index}].burden_id must be a non-empty string")
        updated, rewrite = canonicalize_delta_fields(row)
        if rewrite:
            rows[index] = updated
            delta_rewrites.append(rewrite)
    if delta_rewrites:
        normalization = value.get("normalization")
        if normalization is None:
            normalization = {}
        if not isinstance(normalization, dict):
            raise HarnessError(f"{label}.normalization must be an object when present")
        normalization["per_burden_delta_result_canonicalizations"] = delta_rewrites
        value["normalization"] = normalization


def hydrate_stage06_nar_details(details: Any, canonical_nar: Any) -> None:
    if not isinstance(details, dict):
        raise HarnessError("stage-06 normalized_activation_record_details must be an object when present")
    required = ("n_frame", "live_registers", "burden_floor", "per_burden")
    missing = [key for key in required if key not in details]
    if not missing:
        return
    if not isinstance(canonical_nar, dict):
        raise HarnessError(
            "stage-06 normalized_activation_record_details must include full NAR fields "
            "when normalized_activation_record is not a structured object"
        )
    detail_frame = details.get("n_frame_details")
    if detail_frame is not None:
        if not isinstance(detail_frame, dict):
            raise HarnessError("stage-06 normalized_activation_record_details.n_frame_details must be an object")
        selected = non_empty_string(detail_frame.get("selected"))
        if selected is not None and selected != canonical_nar.get("n_frame"):
            raise HarnessError(
                "stage-06 normalized_activation_record_details.n_frame_details.selected "
                "must match canonical normalized_activation_record.n_frame"
            )
    for key in missing:
        if key not in canonical_nar:
            raise HarnessError(f"stage-06 canonical normalized_activation_record missing {key} for details hydration")
        details[key] = copy.deepcopy(canonical_nar[key])
    normalization = details.get("normalization")
    if normalization is None:
        normalization = {}
    if not isinstance(normalization, dict):
        raise HarnessError("stage-06 normalized_activation_record_details.normalization must be an object when present")
    normalization["hydrated_from_normalized_activation_record"] = missing
    normalization["canonical_n_frame"] = canonical_nar.get("n_frame")
    details["normalization"] = normalization


def list_field(stage: dict[str, Any] | None, key: str) -> list[str]:
    if not isinstance(stage, dict):
        return []
    value = stage.get(key)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def stage04_held_target_burdens(stage04: dict[str, Any] | None) -> set[str]:
    if not isinstance(stage04, dict):
        return set()
    held: set[str] = set()
    for value in list_field(stage04, "held_act_targets"):
        burden_id = canonical_burden_id(value)
        if re.fullmatch(r"B[1-9][0-9]*", burden_id):
            held.add(burden_id)
    for key in ("held_act_details", "hold_partial", "hold_partial_routes", "held_or_partial_routes"):
        value = stage04.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str):
                burden_id = canonical_burden_id(item)
                if re.fullmatch(r"B[1-9][0-9]*", burden_id):
                    held.add(burden_id)
                continue
            if not isinstance(item, dict):
                continue
            raw_burden = item.get("burden_id") or item.get("target") or item.get("land_target")
            if not isinstance(raw_burden, str):
                continue
            burden_id = canonical_burden_id(raw_burden)
            if re.fullmatch(r"B[1-9][0-9]*", burden_id):
                held.add(burden_id)
    return held


def stage_by_id(stages: list[dict[str, Any]], stage_id: str) -> dict[str, Any] | None:
    for stage in stages:
        if stage.get("id") == stage_id:
            return stage
    return None


def canonical_burden_id(value: str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"B[1-9][0-9]*", text):
        return text
    match = re.fullmatch(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}"
    return text


def public_burden_id(value: str) -> str:
    burden = canonical_burden_id(str(value or "").strip())
    if re.fullmatch(r"B[1-9][0-9]*", burden):
        return f"{burden[1:].translate(ASCII_TO_SUP_DIGITS)}B"
    return str(value or "").strip()


def public_submove_id(value: str) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(r"B([1-9][0-9]*)[_\.]([1-9][0-9]*)", text)
    if match:
        return f"{match.group(1).translate(ASCII_TO_SUP_DIGITS)}B{match.group(2).translate(ASCII_TO_SUB_DIGITS)}"
    match = re.fullmatch(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B([₀₁₂₃₄₅₆₇₈₉]+)", text)
    if match:
        return text
    return text


def public_burden_list(values: list[str]) -> str:
    return ", ".join(public_burden_id(value) for value in values)


def body_ref_burden_id(value: str) -> str:
    text = str(value or "").strip()
    match = BODY_REF_BURDEN_RE.fullmatch(text)
    if match:
        return canonical_burden_id(match.group("burden"))
    match = ASCII_BODY_REF_RE.fullmatch(text)
    if match:
        return f"B{match.group('burden')}"
    return ""


def body_ref_completion_flags(all_body_refs: list[str], assigned_body_refs: list[str]) -> dict[str, dict[str, bool]]:
    by_burden: dict[str, list[str]] = {}
    for ref in all_body_refs:
        burden_id = body_ref_burden_id(ref)
        if burden_id:
            by_burden.setdefault(burden_id, []).append(ref)
    assigned = set(assigned_body_refs)
    result: dict[str, dict[str, bool]] = {}
    for burden_refs in by_burden.values():
        for index, ref in enumerate(burden_refs):
            if ref not in assigned:
                continue
            result[ref] = {
                "first_for_burden": index == 0,
                "last_for_burden": index == len(burden_refs) - 1,
            }
    return result


def public_burden_set(values: list[str]) -> str:
    return "{" + public_burden_list(values) + "}" if values else "{}"


def public_graph_value(value: Any) -> str:
    rendered = str(value or "")
    rendered = re.sub(r"\bB[1-9][0-9]*\b", lambda match: public_burden_id(match.group(0)), rendered)
    return rendered.replace("->", "→")


def canonicalize_public_burden_aliases(
    section_role: str,
    text: str,
) -> tuple[str, dict[str, Any] | None]:
    if not text:
        return text, None
    lines = text.splitlines(keepends=True)
    normalized_lines: list[str] = []
    replacements = 0
    in_fence = False

    def bump(pattern: re.Pattern[str], repl: Any, line: str) -> str:
        nonlocal replacements
        normalized, count = pattern.subn(repl, line)
        replacements += count
        return normalized

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            normalized_lines.append(line)
            continue
        if (
            in_fence
            or "⟦ACT" in line
            or "body_ref=" in line
            or PUBLIC_MACHINE_PAYLOAD_LINE_RE.match(line)
        ):
            normalized_lines.append(line)
            continue
        normalized = bump(
            PUBLIC_ASCII_SUBMOVE_RE,
            lambda match: (
                f"{match.group(1).translate(ASCII_TO_SUP_DIGITS)}B"
                f"{match.group(2).translate(ASCII_TO_SUB_DIGITS)}"
                f"{match.group(3) or ''}"
            ),
            line,
        )
        normalized = bump(
            PUBLIC_ASCII_LAND_RE,
            lambda match: f"{match.group(1)}({public_burden_id('B' + match.group(2))})",
            normalized,
        )
        normalized = bump(
            PUBLIC_ASCII_MRP_RE,
            lambda match: f"MRP({public_burden_id('B' + match.group(1))})",
            normalized,
        )
        normalized, reread_count = re.subn(r"\bR\(H,Delta\)", "R(H,Δ)", normalized)
        replacements += reread_count
        normalized = bump(
            PUBLIC_ASCII_EDGE_RE,
            lambda match: (
                f"{public_burden_id('B' + match.group(1))} → "
                f"{public_burden_id('B' + match.group(2))}"
            ),
            normalized,
        )
        normalized = bump(
            PUBLIC_ASCII_BURDEN_RE,
            lambda match: public_burden_id("B" + match.group(1)),
            normalized,
        )
        normalized_lines.append(normalized)
    if replacements == 0:
        return text, None
    normalized_text = "".join(normalized_lines)
    return normalized_text, {
        "role": section_role,
        "canonicalized_public_burden_aliases": True,
        "replacement_count": replacements,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(normalized_text.encode("utf-8")),
    }


def public_graph_line(b_total: list[str], edges: list[dict[str, str]]) -> str:
    graph_line, _roots, _parallel_groups = stage07_dependency_graph_scaffold(b_total, edges)
    return public_graph_value(graph_line)


def burden_id_from_land(land: str) -> str:
    match = LAND_TARGET_RE.search(land)
    return canonical_burden_id(match.group("target")) if match else ""


def stage04_act_details_by_ref(stage04: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    details: dict[str, dict[str, str]] = {}
    for row in list_field(stage04, "act_rows"):
        match = ACT_ROW_DETAIL_RE.match(row)
        if not match:
            continue
        body_ref = match.group("body_ref")
        if body_ref != match.group("body_ref_field"):
            continue
        details[body_ref] = {
            "row": row,
            "body_ref": body_ref,
            "owner": match.group("owner"),
            "operation": match.group("operation"),
            "pressure": match.group("pressure").strip(),
            "delta": match.group("delta").strip(),
            "delta_result": match.group("delta_result").strip(),
            "land": match.group("land").strip(),
            "burden_id": burden_id_from_land(match.group("land")),
        }
    return details


def stage04_owner_routes_by_burden(stage04: dict[str, Any] | None) -> dict[str, list[str]]:
    routes: dict[str, list[str]] = {}
    for detail in stage04_act_details_by_ref(stage04).values():
        burden = detail.get("burden_id") or ""
        owner = detail.get("owner") or ""
        operation = detail.get("operation") or ""
        if not burden or not owner:
            continue
        token = f"{owner}.{operation}" if operation else owner
        routes.setdefault(burden, []).append(token)
    return {burden: ordered_unique(tokens) for burden, tokens in routes.items()}


def matched_owner_route_line(tokens: list[str]) -> str:
    route_tokens = ordered_unique([str(token).strip() for token in tokens if str(token).strip()])
    return "Matched owner/TTP route: " + ", ".join(f"[{token}]" for token in route_tokens)


def stage06_owner_activation_details_by_ref(stage06: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(stage06, dict):
        return {}
    raw = stage06.get("owner_activation_details")
    if not isinstance(raw, list):
        return {}
    details: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        body_ref = item.get("body_ref")
        if isinstance(body_ref, str) and body_ref:
            details[body_ref] = item
    return details


def b_id(value: Any) -> str:
    burden = canonical_burden_id(str(value or "").strip())
    return burden if re.fullmatch(r"B[1-9][0-9]*", burden) else ""


def burden_endpoint_id(value: Any) -> str:
    direct = b_id(value)
    if direct:
        return direct
    text = str(value or "").strip()
    match = re.search(r"(?i)\bMRP\((?P<burden>[^)]+)\)", text)
    return b_id(match.group("burden")) if match else ""


def stage05_generated_burdens(stage05: dict[str, Any] | None) -> list[str]:
    if not isinstance(stage05, dict):
        return []
    raw = stage05.get("generated_burdens")
    generated: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                burden = b_id(item)
            elif isinstance(item, dict):
                burden = b_id(item.get("id") or item.get("burden_id") or item.get("burden") or item.get("target"))
            else:
                burden = ""
            if burden:
                generated.append(burden)
    elif isinstance(raw, dict):
        generated.extend(burden for burden in (b_id(key) for key in raw) if burden)
    return ordered_unique(generated)


GENERATED_MRP_TRACKS = {"primary", "restoration"}


def canonical_generated_mrp_track(value: Any) -> str:
    token = str(value or "").strip().lower().replace("_", "-")
    return token if token in GENERATED_MRP_TRACKS else ""


def generated_burden_track(record: dict[str, Any], route_types: list[str] | None = None) -> str:
    """Classify generated MRP burdens by typed route evidence, not case/prose labels."""
    explicit = canonical_generated_mrp_track(record.get("track"))
    if explicit:
        return explicit
    typed_routes = {str(item or "").strip().lower().replace("_", "-") for item in (route_types or []) if str(item or "").strip()}
    for checked in record_escape_routes(record):
        route_type = str(checked.get("type") or checked.get("route_type") or "").strip().lower().replace("_", "-")
        target = b_id(checked.get("target") or checked.get("burden") or checked.get("generated_target") or record.get("id"))
        live = checked.get("live")
        if route_type == "restoration-recoil" and live is True and (not target or target == b_id(record.get("id"))):
            typed_routes.add(route_type)
    if "restoration-recoil" in typed_routes:
        return "restoration"
    if "generated-burden-instantiation" in typed_routes:
        return "primary"
    return ""


def record_escape_routes(record: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    raw = record.get("escape_routes_checked")
    if isinstance(raw, list):
        routes.extend(item for item in raw if isinstance(item, dict))
    proof = record.get("no_new_resultant_proof")
    if isinstance(proof, dict) and isinstance(proof.get("escape_routes_checked"), list):
        routes.extend(item for item in proof["escape_routes_checked"] if isinstance(item, dict))
    return routes


def stage05_generated_route_types(stage05: dict[str, Any], target: str, record: dict[str, Any]) -> list[str]:
    route_types: list[str] = []
    for key in ("route_type", "mrp_route_result_type"):
        value = str(record.get(key) or "").strip()
        if value:
            route_types.append(value)
    raw_edges = stage05.get("dependency_graph_edges")
    if raw_edges is None and isinstance(stage05.get("dependency_graph"), dict):
        raw_edges = stage05["dependency_graph"].get("edges")
    generated_source = burden_endpoint_id(record.get("generated_by"))
    if isinstance(raw_edges, list):
        for item in raw_edges:
            if not isinstance(item, dict):
                continue
            source = burden_endpoint_id(item.get("from") or item.get("source"))
            edge_target = burden_endpoint_id(item.get("to") or item.get("target"))
            if edge_target != target:
                continue
            edge_type = str(item.get("type") or "").strip()
            if edge_type:
                route_types.append(edge_type)
            elif generated_source and generated_source == source:
                route_types.append("generated_burden_instantiation")
    reread_state = stage05.get("reread_state")
    if isinstance(reread_state, dict):
        route_target = stage07_route_target_from_graph(reread_state.get("graph") or reread_state.get("graph_delta"))
        if route_target == target:
            value = str(reread_state.get("route_result_type") or "").strip()
            if value:
                route_types.append(value)
    raw_resultants = stage05.get("mrp_resultants")
    if isinstance(raw_resultants, list):
        for item in raw_resultants:
            if not isinstance(item, dict):
                continue
            route_target = stage07_route_target_from_graph(item.get("graph") or item.get("graph_delta"))
            if route_target == target:
                value = str(item.get("type") or item.get("route_result_type") or "").strip()
                if value:
                    route_types.append(value)
    return ordered_unique(route_types)


def stage05_generated_burden_records(stage05: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(stage05, dict):
        return []
    raw = stage05.get("generated_burdens")
    if not isinstance(raw, (list, dict)):
        return []
    terminal_states = stage05.get("terminal_states") if isinstance(stage05.get("terminal_states"), dict) else {}
    records: list[dict[str, Any]] = []
    items: list[Any]
    if isinstance(raw, dict):
        items = [{"id": key, **value} if isinstance(value, dict) else {"id": key} for key, value in raw.items()]
    else:
        items = list(raw)
    for item in items:
        if isinstance(item, str):
            burden = b_id(item)
            record: dict[str, Any] = {"id": burden} if burden else {}
        elif isinstance(item, dict):
            burden = b_id(item.get("id") or item.get("burden_id") or item.get("burden") or item.get("target"))
            record = dict(item)
            if burden:
                record["id"] = burden
        else:
            continue
        burden = b_id(record.get("id"))
        if not burden:
            continue
        record["id"] = burden
        record.setdefault("type", "generated_burden")
        record.setdefault("terminal_state", str(terminal_states.get(burden) or "held-with-reason"))
        record.setdefault("activation_state", "generated_unexecuted")
        track = generated_burden_track(record, stage05_generated_route_types(stage05, burden, record))
        if track:
            record.setdefault("track", track)
        depth = record.get("generation_depth")
        if isinstance(depth, str) and depth.isdigit():
            record["generation_depth"] = int(depth)
        elif not isinstance(depth, int):
            record["generation_depth"] = 1
        records.append(record)
    seen: set[str] = set()
    unique_records: list[dict[str, Any]] = []
    for record in records:
        burden = str(record.get("id") or "")
        if burden in seen:
            continue
        seen.add(burden)
        unique_records.append(record)
    return unique_records


def stage05_unresolved_burdens(stage05: dict[str, Any] | None) -> list[str]:
    if not isinstance(stage05, dict):
        return []
    unresolved = [burden for burden in (b_id(item) for item in list_field(stage05, "unresolved_burdens")) if burden]
    proof = stage05.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        unresolved.extend(burden for burden in (b_id(item) for item in list_field(proof, "unresolved_burdens")) if burden)
    return ordered_unique(unresolved)


GENERATED_UNEXECUTED_TERMINAL_STATE = "carried-RECURSE"
GENERATED_UNEXECUTED_REASON = (
    "generated burden has no Stage 04 ACT execution; remains HOLD/PARTIAL/RECURSE"
)
GENERATED_TERMINAL_LIVE_RE = re.compile(
    r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse|owner-body-not-loaded|unexecuted|unresolved)\b"
)
GENERATED_TERMINAL_CLOSED_RE = re.compile(
    r"(?i)^\s*(?:landed|cleared|closed|complete|discharged(?:-as-derivative)?)\s*$"
)


def normalize_stage07_generated_terminal_accounting(
    *,
    generated_burdens: list[str],
    generated_record_by_id: dict[str, dict[str, Any]],
    terminal_states: dict[str, str],
    unresolved_burdens: list[str],
    executed_act_burdens: set[str],
) -> tuple[dict[str, str], list[str]]:
    """Keep generated MRP burdens honest before Stage 07 witness construction."""
    normalized_states = dict(terminal_states)
    unresolved = list(unresolved_burdens)
    for burden in generated_burdens:
        record = generated_record_by_id.setdefault(
            burden,
            {
                "id": burden,
                "type": "generated_burden",
                "generation_depth": 1,
            },
        )
        if burden in executed_act_burdens:
            record["activation_state"] = "generated_executed"
            record.setdefault("terminal_state", str(normalized_states.get(burden) or "landed"))
            track = generated_burden_track(record)
            if track:
                record.setdefault("track", track)
            continue

        current_state = str(
            normalized_states.get(burden)
            or record.get("terminal_state")
            or ""
        ).strip()
        if (
            not current_state
            or GENERATED_TERMINAL_CLOSED_RE.fullmatch(current_state)
            or GENERATED_TERMINAL_LIVE_RE.search(current_state) is None
        ):
            current_state = GENERATED_UNEXECUTED_TERMINAL_STATE
        normalized_states[burden] = current_state
        record["terminal_state"] = current_state
        record["activation_state"] = "generated_unexecuted"
        record.setdefault("reason", GENERATED_UNEXECUTED_REASON)
        track = generated_burden_track(record)
        if track:
            record.setdefault("track", track)
        unresolved.append(burden)
    return normalized_states, ordered_unique(unresolved)


def stage05_dependency_edges(stage05: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(stage05, dict):
        return []
    generated_sources: dict[str, str] = {}
    generated_targets = set(stage05_generated_burdens(stage05))
    for record in stage05_generated_burden_records(stage05):
        target = b_id(record.get("id") or record.get("burden_id") or record.get("target"))
        if not target:
            continue
        generated_targets.add(target)
        source = burden_endpoint_id(
            record.get("generated_by")
            or record.get("source")
            or record.get("parent")
            or record.get("generated_from")
        )
        if source:
            generated_sources[target] = source
    raw = stage05.get("dependency_graph_edges")
    if raw is None:
        graph = stage05.get("dependency_graph")
        raw = graph.get("edges") if isinstance(graph, dict) else None
    if not isinstance(raw, list):
        return []
    edges: list[dict[str, str]] = []
    for item in raw:
        edge_type = "held_burden_activation"
        if isinstance(item, dict):
            source = burden_endpoint_id(item.get("from") or item.get("source"))
            target = burden_endpoint_id(item.get("to") or item.get("target"))
            if isinstance(item.get("type"), str) and item["type"].strip():
                edge_type = item["type"].strip()
        elif isinstance(item, list) and len(item) == 2:
            source = burden_endpoint_id(item[0])
            target = burden_endpoint_id(item[1])
        elif isinstance(item, str):
            match = re.search(
                r"(?P<source>B[1-9][0-9]*|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s*(?:->|→)\s*"
                r"(?P<target>B[1-9][0-9]*|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)",
                item,
            )
            if not match:
                continue
            source = burden_endpoint_id(match.group("source"))
            target = burden_endpoint_id(match.group("target"))
        else:
            continue
        if source and target:
            generated_source = generated_sources.get(target)
            if target in generated_targets and (not generated_source or generated_source == source):
                edge_type = "generated_burden_instantiation"
            edges.append({"from": source, "to": target, "type": edge_type})
    return edges


STAGE02_BURDEN_REGISTER_KEYS = ("register_types", "registers", "burden_types", "types")


def field_witness_registers_in_text(value: object) -> list[str]:
    """Project Stage 02 register prose into the Stage 07 field_witness dialect."""

    source = str(value or "").strip()
    if not source:
        return []
    return checker_field_witness_registers_in_text(source)


def field_witness_registers_from_values(values: list[object]) -> list[str]:
    registers: list[str] = []
    for value in values:
        registers.extend(field_witness_registers_in_text(value))
    return ordered_unique(registers)


def stage02_burden_detail_registers(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in STAGE02_BURDEN_REGISTER_KEYS:
        registers = item.get(key)
        if not isinstance(registers, list):
            continue
        values.extend(str(register).strip() for register in registers if str(register).strip())
    return ordered_unique(values)


def stage02_detail_register_projection(item: dict[str, Any]) -> list[str]:
    explicit = stage02_burden_detail_registers(item)
    if explicit:
        return field_witness_registers_from_values(explicit)
    scalars: list[object] = []
    for value in item.values():
        if isinstance(value, str):
            scalars.append(value)
        elif isinstance(value, list):
            scalars.extend(entry for entry in value if isinstance(entry, str))
    return field_witness_registers_from_values(scalars)


def stage02_live_register_fallback_coverage(stage02: dict[str, Any] | None, burdens: list[str]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {}
    for burden, raw in zip(burdens, list_field(stage02, "live_registers")):
        for register in field_witness_registers_in_text(raw):
            coverage.setdefault(register, []).append(burden)
    return coverage


def stage02_register_coverage(stage02: dict[str, Any] | None, burdens: list[str]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {}
    if isinstance(stage02, dict):
        details = stage02.get("burden_floor_details") or stage02.get("burden_floor_detail")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict):
                    continue
                burden = b_id(item.get("burden_id") or item.get("id"))
                registers = stage02_detail_register_projection(item)
                if not burden or not registers:
                    continue
                for register in registers:
                    coverage.setdefault(register, []).append(burden)
    fallback_coverage = stage02_live_register_fallback_coverage(stage02, burdens)
    for register, ids in fallback_coverage.items():
        if register not in coverage:
            coverage[register] = ids
    if coverage:
        return {register: ordered_unique(ids) for register, ids in coverage.items()}
    return {}


def stage02_burden_register_types(stage02: dict[str, Any] | None, burdens: list[str]) -> dict[str, list[str]]:
    burden_registers: dict[str, list[str]] = {}
    if isinstance(stage02, dict):
        details = stage02.get("burden_floor_details") or stage02.get("burden_floor_detail")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict):
                    continue
                burden = b_id(item.get("burden_id") or item.get("id"))
                values = stage02_detail_register_projection(item)
                if not burden or not values:
                    continue
                burden_registers[burden] = values
    for burden, raw in zip(burdens, list_field(stage02, "live_registers")):
        if burden in burden_registers:
            continue
        registers = field_witness_registers_in_text(raw)
        if registers:
            burden_registers[burden] = registers
    if burden_registers:
        return burden_registers
    return {}


def stage02_public_live_registers(stage02: dict[str, Any] | None, burdens: list[str]) -> list[str]:
    live_registers = field_witness_registers_from_values(list_field(stage02, "live_registers"))
    coverage = stage02_register_coverage(stage02, burdens)
    return ordered_unique([*live_registers, *coverage.keys()])


def stage02_diagnostic_ir_details(stage02: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(stage02, dict):
        return {}
    details = stage02.get("diagnostic_ir_details")
    return details if isinstance(details, dict) else {}


def stage07_layer_a_diagnostic_state_lines(stage02: dict[str, Any] | None) -> list[str]:
    details = stage02_diagnostic_ir_details(stage02)
    if not details and not isinstance(stage02, dict):
        return []
    lines: list[str] = []

    def add(label: str, value: Any) -> None:
        if isinstance(value, list):
            rendered = "; ".join(str(item).strip() for item in value if str(item).strip())
        else:
            rendered = str(value).strip() if value is not None else ""
        if rendered:
            lines.append(f"{label}: {rendered}")

    add("Field", details.get("field") or (stage02 or {}).get("field"))
    add("Task", details.get("user_task") or (stage02 or {}).get("user_task"))
    add("Authority frame", details.get("authority_frame"))
    add("Claim level", details.get("claim_level"))
    add("Selected N-frame", (stage02 or {}).get("selected_n_frame"))
    add("Held N-frame candidates", (stage02 or {}).get("held_n_frame_candidates"))
    add("Pattern profile", details.get("pattern_profile"))
    add("DO orientation", details.get("do_orient") or details.get("do_orientation"))
    add("Concealment mode", details.get("concealment_mode"))
    add("Diagnostic deformation", details.get("deformation"))
    return lines


def stage07_route_type_for_burden(
    burden: str,
    edges: list[dict[str, str]],
    final_source: str,
    final_type: str,
) -> str:
    if burden == final_source and final_type:
        return final_type
    for edge in edges:
        if burden in {edge["from"], edge["to"]}:
            return edge.get("type") or "held_burden_activation"
    return "no_new_resultant"


def stage07_held_or_partial_burdens(
    b_total: list[str],
    terminal_states: dict[str, str],
    unresolved_burdens: list[str],
) -> list[str]:
    unresolved = set(unresolved_burdens)
    return [
        burden
        for burden in b_total
        if burden in unresolved
        or re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            terminal_states.get(burden, ""),
        )
        is not None
    ]


def stage07_dependency_graph_scaffold(
    b_total: list[str],
    edges: list[dict[str, str]],
) -> tuple[str, list[str], list[list[str]]]:
    if not b_total:
        return "none", [], []
    if edges:
        incoming = {edge["to"] for edge in edges}
        roots = [burden for burden in b_total if burden not in incoming]
        graph_segments = [f"{root} (root)" for root in roots]
        graph_segments.extend(f"{edge['from']} -> {edge['to']}" for edge in edges)
        return "; ".join(graph_segments), roots, []
    roots = list(b_total)
    parallel_groups = [list(b_total)] if len(b_total) > 1 else []
    return " || ".join(f"{burden} (root)" for burden in b_total), roots, parallel_groups


def stage07_route_target_from_graph(value: Any) -> str:
    match = re.search(r"\bB[1-9][0-9]*\s*(?:->|→)\s*(B[1-9][0-9]*)\b", str(value or ""))
    return match.group(1) if match else ""


def stage07_stop_proof(source: str) -> dict[str, Any]:
    return {
        "escape_routes_checked": [
            {
                "type": "closure-boundary-immunity",
                "live": False,
                "basis": f"MRP({source}) reported no new closure-boundary-immunity route after R(H,Delta).",
            },
            {
                "type": "proof-carousel",
                "live": False,
                "basis": f"MRP({source}) reported no proof-carousel route after the terminal reread.",
            },
            {
                "type": "total-system-exhaustion",
                "live": False,
                "basis": "The bounded Stage 07 reply licenses only this scoped terminal state, not a global total-system proof.",
            },
            {
                "type": "doubt-churn",
                "live": False,
                "basis": f"MRP({source}) reports neutral divergence and null curl at STOP.",
            },
            {
                "type": "moral-tribunal",
                "live": False,
                "basis": f"MRP({source}) did not expose a live moral-tribunal route.",
            },
            {
                "type": "authority-order-recoil",
                "live": False,
                "basis": f"MRP({source}) did not expose a live authority-order recoil route.",
            },
            {
                "type": "hidden-framework-recoil",
                "live": False,
                "basis": f"MRP({source}) did not expose a live hidden-framework recoil route.",
            },
            {
                "type": "restoration-recoil",
                "subtype": "scope-protest",
                "live": False,
                "basis": f"MRP({source}) did not expose a live restoration-recoil route.",
            },
        ],
        "field_state_at_stop": {
            "divergence": "neutral",
            "curl": "null",
            "b_live": "empty",
            "kappa_residual": 0,
        },
        "stop_licensed": True,
    }


def per_burden_state_head(value: Any, prefix_re: re.Pattern[str]) -> str:
    body = staged_output.per_burden_diag_body(str(value or ""), prefix_re)
    return body.partition("/")[0].strip()


def has_raw_machine_burden(value: Any, burden_id: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(burden_id)}(?![A-Za-z0-9_])", str(value or "")) is not None


def stage07_formal_delta(value: Any, source: str) -> str:
    text = str(value or "").strip()
    if not text or has_raw_machine_burden(text, source):
        return text
    if re.fullmatch(r"B[1-9][0-9]*", source):
        public = staged_output.public_burden_token(source[1:])
        public_delta = f"Δ{public}"
        if text.startswith(public_delta):
            rest = text[len(public_delta):].lstrip()
            if rest.startswith(":"):
                rest = rest[1:].lstrip()
                return f"{public_delta} / Delta({source}): {rest}"
        return f"{text} / Delta({source})"
    return text


def stage07_formal_divergence_state(entry: dict[str, Any], route_type: str, route: str) -> str:
    head = per_burden_state_head(entry.get("divergence"), staged_output.PER_BURDEN_DIVERGENCE_PREFIX_RE)
    if (route_type in {"no_new_resultant", "none", "stable"} or route.upper() == "STOP") and head in {
        "settled",
        "bounded",
        "non-neutral",
    }:
        return "neutral"
    return head


def stage07_formal_curl_state(entry: dict[str, Any], route_type: str, route: str) -> str:
    head = per_burden_state_head(entry.get("curl"), staged_output.PER_BURDEN_CURL_PREFIX_RE)
    if (route_type in {"no_new_resultant", "none", "stable"} or route.upper() == "STOP") and head in {
        "resolved",
        "held",
        "non-null",
    }:
        return "null"
    return head


def stage07_formal_route_gradient(entry: dict[str, Any], route_type: str, target: str) -> str:
    gradient = str(entry.get("route_gradient") or "")
    if (
        route_type == "held_burden_activation"
        and target
        and not has_raw_machine_burden(gradient, target)
        and re.search(r"(?i)\b(?:already[- ]held|held|B_LA|initial)\b", gradient) is None
    ):
        return gradient.rstrip() + f" already-held {target} from B_LA."
    return gradient


def stage05_per_burden_entries(stage05: dict[str, Any] | None) -> list[dict[str, Any]]:
    entries = stage05.get("per_burden_reread") if isinstance(stage05, dict) else None
    if (
        not isinstance(entries, list)
        or not entries
        or not all(isinstance(entry, dict) for entry in entries)
    ):
        raise HarnessError(
            "stage-05 per_burden_reread records are required to derive visible MRP structure; "
            "Stage 07 never synthesizes findings, rereads, or pressure slots from edges, "
            "terminal states, or prose"
        )
    return [dict(entry) for entry in entries]


def stage05_mrp_route_types_by_burden(stage05: dict[str, Any] | None) -> dict[str, set[str]]:
    entries = stage05.get("per_burden_reread") if isinstance(stage05, dict) else None
    if not isinstance(entries, list):
        return {}
    result: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        burden_id = str(entry.get("burden_id") or "").strip()
        route_type = str(entry.get("route_result_type") or "").strip()
        if burden_id and route_type:
            result.setdefault(burden_id, set()).add(route_type)
    return result


def stage06_nar_objects(stage06: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    for key in ("normalized_activation_record", "normalized_activation_record_details"):
        value = stage06.get(key)
        if isinstance(value, dict):
            result.append((key, value))
    return result


def validate_stage06_nar_route_types_against_stage05(stage05: dict[str, Any], stage06: dict[str, Any]) -> None:
    expected_by_burden = stage05_mrp_route_types_by_burden(stage05)
    if not expected_by_burden:
        return
    for nar_label, nar in stage06_nar_objects(stage06):
        rows = nar.get("per_burden")
        if not isinstance(rows, list):
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            burden_id = str(row.get("burden_id") or "").strip()
            if not burden_id:
                continue
            expected = expected_by_burden.get(burden_id)
            route_type = str(row.get("mrp_route_result_type") or row.get("route_result_type") or "").strip()
            if route_type and expected and route_type not in expected:
                expected_text = ", ".join(sorted(expected))
                raise HarnessError(
                    f"stage-06 {nar_label}.per_burden[{index}].mrp_route_result_type "
                    f"must match stage-05 per_burden_reread route_result_type(s) for {burden_id}: "
                    f"{expected_text}; got {route_type}"
                )


def mrp_resultant_rows_from_entries(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "source": str(entry.get("burden_id") or ""),
            "type": str(entry.get("route_result_type") or ""),
            "finding": str(entry.get("finding") or ""),
            "graph": str(entry.get("graph_delta") or ""),
            "route": str(entry.get("route") or ""),
        }
        for entry in entries
    ]


def self_test_reread_entry(
    burden_id: str,
    *,
    next_burden_id: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    entry = staged_output.self_test_per_burden_entry(burden_id, next_burden_id=next_burden_id)
    entry.update(overrides)
    return entry


def self_test_reread_hold_entry(burden_id: str) -> dict[str, Any]:
    public = staged_output.public_burden_token(burden_id[1:])
    return self_test_reread_entry(
        burden_id,
        reread=(
            f"R(H,Δ): held routes rechecked: {public}; live remainder: {public}; release/next: HOLD."
        ),
        route_gradient=(
            f"plain-gradient holds {public} as HOLD/PARTIAL after R(H,Δ); no new graph edge is licensed."
        ),
        divergence="∇·B: non-neutral / held burden remains live",
        curl="∇×κ: held / held burden remains live",
        finding="partial-real",
        route_result_type="hold_partial",
        mrp_resultant=f"partial-real -> no new graph edge; HOLD {public}",
        graph_delta="none",
        preemption_basis="none",
        route="HOLD",
    )


def self_test_reread_generated_entry(parent: str, generated: str) -> dict[str, Any]:
    parent_public = staged_output.public_burden_token(parent[1:])
    generated_public = staged_output.public_burden_token(generated[1:])
    return self_test_reread_entry(
        parent,
        reread=(
            f"R(H,Δ): held routes rechecked: {generated_public}; live remainder: {generated_public}; "
            f"release/next: RECURSE to {generated_public}."
        ),
        route_gradient=(
            f"newly generated {generated_public} [generated-by: MRP({parent_public})] is absent from "
            f"B_LA after Δ {parent_public} post-Land field-pressure."
        ),
        divergence="∇·B: non-neutral / generated burden remains live",
        curl="∇×κ: held / generated burden hold",
        finding="genuine-dependent",
        route_result_type="generated_burden_instantiation",
        mrp_resultant=f"genuine-dependent -> graph {parent} -> {generated}; RECURSE",
        graph_delta=f"{parent} -> {generated}",
        preemption_basis="graph-bound",
        route="RECURSE",
    )


def stage07_formal_reread_states(
    per_burden_reread: list[dict[str, Any]],
    terminal_states: dict[str, str],
    unresolved_burdens: list[str] | None = None,
    owner_routes_by_burden: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Project stage-05 per_burden_reread records into formal_reread_states rows.

    Rows are 1:1 projections of the producer records (current key schema, no new
    keys); this function adds accounting metadata only and never invents reread
    content.
    """
    if not isinstance(per_burden_reread, list) or not per_burden_reread:
        raise HarnessError(
            "stage07_formal_reread_states requires stage-05 per_burden_reread records; "
            "formal_reread_states rows are 1:1 projections and are never synthesized"
        )
    states: list[dict[str, Any]] = []
    unresolved = set(unresolved_burdens or [])
    owner_routes = owner_routes_by_burden or {}

    def held_terminal(state_value: str) -> bool:
        return re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            state_value,
        ) is not None

    field_held_burdens = sorted(
        set(unresolved)
        | {
            burden_id
            for burden_id, state_value in terminal_states.items()
            if held_terminal(str(state_value or ""))
        }
    )
    for entry in per_burden_reread:
        source = str(entry.get("burden_id") or "")
        if not source:
            continue
        route_type = str(entry.get("route_result_type") or "")
        route = str(entry.get("route") or "")
        graph = str(entry.get("graph_delta") or "")
        terminal_state = terminal_states.get(source, "landed")
        held_or_partial = source in unresolved or held_terminal(terminal_state)
        target = stage07_route_target_from_graph(graph)
        state: dict[str, Any] = {
            "source_burden": source,
            "prior_land": f"Land({source}): terminal state {terminal_state}.",
            "delta": stage07_formal_delta(entry.get("landed_delta"), source),
            "reread": "R(H,Delta)",
            "divergence_state": stage07_formal_divergence_state(entry, route_type, route),
            "curl_state": stage07_formal_curl_state(entry, route_type, route),
            "route_result_type": route_type,
            "mrp_resultant": str(entry.get("mrp_resultant") or ""),
            "graph_delta": graph,
            "preemption_basis": str(entry.get("preemption_basis") or ""),
            "route": route,
            "route_gradient": stage07_formal_route_gradient(entry, route_type, target),
        }
        if route_type == "held_burden_activation":
            if target:
                state["next_burden"] = target
            state["owner_route"] = owner_routes.get(target) or ["held"]
        elif route_type == "generated_burden_instantiation":
            if target:
                state["next_burden"] = target
            state["owner_route"] = owner_routes.get(target) or ["generated"]
            state["generated_by"] = f"MRP({source})"
        elif route_type == "no_new_resultant" or route.upper() == "STOP":
            if held_or_partial:
                state["no_new_resultant_proof"] = {
                    "escape_routes_checked": [],
                    "proved": False,
                    "basis": (
                        f"{source} remains {terminal_state}; no-new-resultant STOP is not licensed "
                        "for coverage completion while the burden is unresolved."
                    ),
                }
            elif field_held_burdens:
                state["no_new_resultant_proof"] = {
                    "escape_routes_checked": [],
                    "proved": False,
                    "basis": (
                        f"MRP({source}) STOP is burden-local only; field-level no-new-resultant is not "
                        f"licensed while {', '.join(field_held_burdens)} remain(s) held/unresolved."
                    ),
                }
            else:
                state["no_new_resultant_proof"] = stage07_stop_proof(source)
        states.append(state)
    return states


def stage07_mrp_landed_delta(source: str, terminal_state: str, route_type: str) -> str:
    return f"Delta {source}: terminal state {terminal_state}; MRP route result type {route_type}."


def stage07_mrp_reread_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    if not isinstance(stage05, dict) or not stage05:
        return ""
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    generated_records = stage05_generated_burden_records(stage05)
    generated_burdens = ordered_unique(
        [*stage05_generated_burdens(stage05), *[str(record.get("id") or "") for record in generated_records if record.get("id")]]
    )
    generated_record_by_id = {str(record.get("id")): dict(record) for record in generated_records if record.get("id")}
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    act_owner_routes_by_burden = stage04_owner_routes_by_burden(stage04)
    executed_act_burdens = set(act_owner_routes_by_burden)
    owner_routes_by_burden = dict(act_owner_routes_by_burden)
    terminal_states_raw = stage05.get("terminal_states")
    terminal_states = terminal_states_raw if isinstance(terminal_states_raw, dict) else {}
    terminal_states = {
        burden: str(terminal_states.get(burden) or "landed")
        for burden in b_total
    }
    edges = stage05_dependency_edges(stage05)
    unresolved_burdens = stage05_unresolved_burdens(stage05)
    terminal_states, unresolved_burdens = normalize_stage07_generated_terminal_accounting(
        generated_burdens=generated_burdens,
        generated_record_by_id=generated_record_by_id,
        terminal_states=terminal_states,
        unresolved_burdens=unresolved_burdens,
        executed_act_burdens=executed_act_burdens,
    )
    per_burden_entries = stage05_per_burden_entries(stage05)
    mrp_resultants = mrp_resultant_rows_from_entries(per_burden_entries)

    for edge in edges:
        target = edge["to"]
        if target not in generated_burdens:
            continue
        record = generated_record_by_id.setdefault(
            target,
            {
                "id": target,
                "type": "generated_burden",
                "generation_depth": 1,
                "terminal_state": terminal_states.get(target, "held-with-reason"),
            },
        )
        record.setdefault("generated_by", f"MRP({edge['from']})")
        track = generated_burden_track(record, [edge.get("type", "")])
        if track:
            record.setdefault("track", track)

    def route_tokens_for_burden(target: str) -> list[str]:
        tokens = list(owner_routes_by_burden.get(target) or [])
        record = generated_record_by_id.get(target, {})
        raw_route = record.get("required_owner_route")
        if isinstance(raw_route, list):
            tokens.extend(str(item).strip() for item in raw_route if str(item).strip())
        elif isinstance(raw_route, str) and raw_route.strip():
            tokens.append(raw_route.strip())
        return ordered_unique(tokens)

    def matched_route_line(target: str) -> str:
        tokens = route_tokens_for_burden(target)
        if not tokens:
            return "Matched owner/TTP route: [held] source-owned route pending explicit ACT execution"
        return "Matched owner/TTP route: " + ", ".join(f"[{token}]" for token in tokens)

    def generated_heading_lines() -> list[str]:
        lines: list[str] = []
        for burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            generated_by = str(record.get("generated_by") or "")
            source = b_id(generated_by.replace("MRP(", "").replace(")", ""))
            if not source:
                for edge in edges:
                    if edge["to"] == burden:
                        source = edge["from"]
                        generated_by = f"MRP({source})"
                        break
            if not source:
                continue
            state = terminal_states.get(burden, "held-with-reason")
            title = str(record.get("title") or record.get("reason") or "generated MRP burden").strip()
            public_burden = public_burden_id(burden)
            public_source = public_burden_id(source)
            lines.extend(
                [
                    f"## Burden {burden[1:]} / {public_burden} [generated-by: MRP({public_source})] — {title}",
                    "### Layer A — Generated Burden Accounting",
                    f"- live noetic burden: {public_burden} [generated-by: MRP({public_source})]",
                    f"- generated status: not in 𝔅_LA; present in 𝔅_MRP; terminal_state={state}",
                    f"- {matched_route_line(burden)}",
                ]
            )
            if burden in executed_act_burdens:
                lines.append(
                    f"Land({public_burden}): generated MRP burden has visible Stage 04 ACT execution; "
                    "its landed/terminal status must match owner activations, MRP, and field_witness."
                )
            else:
                lines.append(
                    f"HOLD({public_burden}): generated MRP burden remains unresolved/unexecuted unless Stage 04 ACT rows actually execute it; "
                    "coverage_complete=false; route remains HOLD/PARTIAL/RECURSE."
                )
        return lines

    terminal_lines = [
        f"{public_burden_id(burden)}: {terminal_states.get(burden, 'landed')}"
        for burden in b_total
    ]
    preview_lines: list[str] = []
    for entry in per_burden_entries:
        preview_lines.extend(staged_output.render_mrp_block(entry).splitlines())
        preview_lines.append("")
    ledger_lines = [
        "MRP terminal reconstruction floor:",
        "Route-state ledger:",
        *[
            f"- MRP({public_burden_id(row['source'])}): type={row['type']}; finding={row['finding']}; "
            f"graph={public_graph_value(row['graph'])}; route={row['route']}"
            for row in mrp_resultants
        ],
        *generated_heading_lines(),
        "Terminal states:",
        *terminal_lines,
    ]
    lines = [
        "",
        "Stage 07 per-burden MRP visibility contract:",
        "- The harness injects one canonical `[Mid-Reread Pressure]` block immediately after each line-start superscript `Land(ⁿB):` landing gate, rendered verbatim from the Stage 05 `per_burden_reread` records. Do NOT print any `[Mid-Reread Pressure]` heading or block yourself, in any section; a model-authored heading fails assembly.",
        "- In the Layer B / ACT sections, print exactly one line-start superscript landing gate per terminal burden, for example `Land(¹B): landed.`; machine ⟦ACT⟧ rows and ASCII `Land(B1)` aliases do not count as public landing gates.",
        "- Every landing gate must match one Stage 05 per_burden_reread record and every record must match one gate; assembly fails on either mismatch or on a duplicate gate.",
        "- Harness-injected blocks for this case (reference only; never print these yourself):",
        *[f"  {line}" for line in preview_lines],
        "- The MRP/reread/terminal section is ledger-only: print the reconstruction floor, route-state ledger, and terminal states below; no `[Mid-Reread Pressure]` heading block:",
        *[f"  {line}" for line in ledger_lines],
        "- `field_witness.formal_reread_states[]` and `field_witness.mrp_resultants[]` must mirror the Stage 05 per_burden_reread records 1:1: same burden order, `route_result_type`, graph delta, and route; `formal_reread_states[].delta` preserves the public `landed_delta` notation while also carrying machine `Delta(Bn)` identity.",
        "- Do not rely on a later `MRP(ⁿB): ...` closure-ledger row as the only public MRP evidence; the harness-injected blocks carry the public per-burden reread proof.",
    ]
    return "\n".join(lines)


def stage07_layer_a_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    if not burden_floor:
        return ""
    generated_burdens = stage05_generated_burdens(stage05)
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    live_registers = stage02_public_live_registers(stage02, burden_floor)
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    diagnostic_lines = stage07_layer_a_diagnostic_state_lines(stage02)
    burden_rows = []
    for burden in burden_floor:
        registers = burden_registers.get(burden, [])
        register_text = ", ".join(registers) if registers else "register-types-from-Stage-02"
        burden_rows.append(f"{public_burden_id(burden)} [{register_text}] status=initial-live")

    visible_lines = [
        f"Live registers: {', '.join(live_registers)}" if live_registers else "Live registers: none",
        f"Initial burden set: [{public_burden_list(burden_floor)}]",
        f"𝔅_LA (B_LA) = {public_burden_set(burden_floor)}",
        f"𝔅_MRP (B_MRP) = {public_burden_set(generated_burdens)}",
        f"𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {public_burden_set(b_total)}",
        "Layer A burden/register rows:",
        *burden_rows,
    ]
    lines = [
        "",
        "Stage 07 Layer A parser-stable contract:",
        "- Print these checker-owned Layer A lines near the top of the Layer A section before prose expansion:",
        *[f"  {line}" for line in visible_lines],
        "- Do not replace `Initial burden set: [...]` with `Initial burden set ledger:`; prose ledgers may follow only after the exact line exists.",
        "- `𝔅_LA (B_LA)` must equal the initial burden set; `𝔅_MRP (B_MRP)` must contain only Stage 05 generated burdens and must be `{}` when there are none.",
        "- `𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required exactly as the public total-ledger relation, followed by the concrete public burden set.",
        "- Each Layer A burden/register row must expose the burden ID and its Stage 02 register type(s) so the field witness can prove live-register floor coverage.",
    ]
    if diagnostic_lines:
        lines.extend(
            [
                "- Print these Stage 02 diagnostic-state projection lines exactly before prose expansion:",
                *[f"  {line}" for line in diagnostic_lines],
            ]
        )
        concealment_line = next(
            (line for line in diagnostic_lines if line.lower().startswith("concealment mode:")),
            "",
        )
        if "mixed" in concealment_line.lower() and len(concealment_source_components(concealment_line)) >= 2:
            components = ", ".join(concealment_source_components(concealment_line))
            lines.append(
                "- Because Stage 02 selected mixed concealment, the `Concealment mode:` line must name "
                f"at least two source-owned component pressures in that same line: {components}. "
                "Do not collapse this to generic `mixed pressure`."
            )
    return "\n".join(lines)


def stage07_act_contract_guidance(
    previous_stages: list[dict[str, Any]],
    assigned_body_refs: list[str],
) -> str:
    if not assigned_body_refs:
        return ""
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    act_details = stage04_act_details_by_ref(stage04)
    owner_details = stage06_owner_activation_details_by_ref(stage06)
    all_body_refs = list_field(stage04, "act_body_refs")
    completion_flags = body_ref_completion_flags(all_body_refs, assigned_body_refs)
    missing = [ref for ref in assigned_body_refs if ref not in act_details]
    if missing:
        raise HarnessError(f"compiled Stage 07 ACT prompt missing canonical Stage 04 row(s): {missing}")

    lines = [
        "",
        "Stage 07 NLA semantic-faithfulness contract for this ACT slice:",
        "- Copy these canonical Stage 04 ACT rows exactly; do not rewrite their owner, operation, pressure, delta, body_ref, or Land slots:",
    ]
    lines.extend(f"  {act_details[ref]['row']}" for ref in assigned_body_refs)
    lines.extend(
        [
            "- Do not write malformed rows such as `⟦ACT [owner.operation] ...⟧`; the body_ref must appear immediately after `ACT`.",
            "- Do not write any ACT-looking summary row outside this ACT slice. If a line begins with `⟦ACT`, it must be one of the exact copied Stage 04 rows above and it must include `body_ref=`.",
            "- After each copied ACT row, emit exactly one dereferenceable public submove block for the same body_ref.",
            "- Public submove block headings must use canonical public notation such as `¹B₁[owner] - ...`, not ASCII `B1_1[owner]`; keep ASCII `body_ref=B1_1` only inside copied ACT rows and field_witness JSON.",
            "- Emit a `## Burden N / ⁿB` heading only when this section contains the first Stage 04 body_ref for that burden.",
            "- If this section continues a burden started in the prior ACT slice, continue with the next submove only; do not repeat the burden heading.",
            "- Each submove block heading must begin with that canonical public submove ID plus `[{owner}] - ...` with the owner token only; put the operation in the `Operation:` facet.",
            "- Each submove block must contain `Target:`, `Operation:`, `Result/state-change:`, and `Contribution-to-Land(Bn):` facets.",
            "- The block prose must make the ACT pressure, operation, delta/result, and Land(Bn) contribution recoverable without relying on the ACT row alone.",
            "- Stage07 locality rule: every landed ACT row must make a local proof capsule recoverable near that row: BEFORE (what pressure/state was live), OPERATION (which owner operation acted), AFTER (what changed in this burden), DELTA (how the compact delta_result names it), and LAND-LICENSE (why Land(Bn) is licensed instead of HOLD/PARTIAL).",
            "- For every landed row, `Contribution-to-Land(Bn):` must include the local LAND-LICENSE: it must say why this row licenses `Land(Bn)` because the named burden-local state changed. Do not write a generic contribution such as `this submove bounds the carrier function` without the concrete Land license.",
            "- Copy the ACT Land slot byte-for-byte from the canonical Stage 04 row. Do not rewrite `Land(B5)+` / `Land(⁵B)+` into prose such as `Land(additional burden 5)+`; a prose Land target is not a typed burden id.",
            "- The ACT owner, matched route owner, submove owner heading, field_witness owner, and NAR owner_id must all name the same callable selected owner family; route/context umbrella labels, case-library labels, noetic-frame labels, and code lookups are not load-bearing ACT owners.",
            "- If the selected route names only an umbrella/context module, resolve to a callable owner/TTP floor before ACT; otherwise keep the route as HOLD/PARTIAL instead of inventing an ACT owner.",
            "- If the matched owner body is not loaded, emit HOLD/PARTIAL with `OWNER-BODY-NOT-LOADED` and do not emit `Land(Bn):` for that burden.",
            "- The `TTP Operation Body:` must visibly perform target -> operation -> result -> contribution; do not merely restate the conclusion, cite an owner name, or summarize that the burden fails.",
            "- Operation-token discipline: keep the registered callable operation token from the copied ACT row and skeleton. Do not replace it with a result, pressure, route label, or prose description; result labels belong in `Result/state-change:` and local prose.",
            "- Delta-layer discipline: the ACT `Δ=` carrier before the colon must be only a burden-state delta such as `Δ¹B` / `ΔB1` or dependency-radius `Δκ`; never print `D7`, `D8`, `Δ¹B₁`, `ΔB1_1`, owner.operation, register axes, or prose labels as the carrier.",
            "- Keep `delta_result` as the owner-local suffix after the colon and in `Result/state-change:`; the carrier proves which hidden transition state changed, while the suffix names what changed locally.",
            "- If the row needs κ/H dependency-radius work, use `Δκ:<owner-local-state-change>` and make the dependency-radius change visible in the dereferenced body; otherwise use the burden-state carrier `ΔⁿB:<owner-local-state-change>`.",
            "- A compact label such as `reopen-condition-stated` or `scope-boundary-named` cannot replace the visible burden-local state change; if the body cannot show the state transition, route HOLD/PARTIAL instead of printing `Land(Bn)`.",
            "- Source/citation/proof-stack rows must name the concrete burden-local state change that the source-status, authority-order, proof-method, or transmission/content operation produces.",
            "- For compact `typed` deltas, the public `Result/state-change:` facet must include checker-stable state-change language such as `State change: ... classified`, `... exposed`, or `no longer treated as ...`; the delta token alone is not a state change.",
            "- For `proof-method-audit.proof-family-and-carrier-audit`, the dereferenced body must audit the proof family/carrier by naming the premise or predicate set, inference grammar, conclusion scope, and visible state change. Use a parser-stable result phrase such as `State change: the proof carrier is classified as a proof carrier whose premise set, inference grammar, and conclusion scope are no longer treated as a neutral proof.`",
            "- For `proof-method-audit.proof-route-status-audit`, the dereferenced body must identify the proof forum, standard of proof, tribunal/burden-function, proof eligibility, supporting texts, and premise/inference/conclusion scope. Generic proof-route labels do not Land.",
            "- For `pattern-profiling.loaded-label-carrier-audit`, the dereferenced body must identify the label as a noetic/worldview/identity carrier, expose the hidden proof/source/authority rule it transmits, and show `carrier-function-typed` as a burden-local state transition. Owner and delta labels alone do not Land.",
            "- For `pattern-profiling.loaded-label-carrier-audit`, the `Result/state-change:` facet must say the loaded label carrier function is exposed or classified; do not rely on `carrier-function-typed` by itself.",
            "- For `pattern-profiling.proof-packet-reconstruction`, the dereferenced body must reconstruct the proof packet, expose hidden source moves, predicate transfers, conclusion jumps, or forum switches, and show `proof-packet-reconstructed` as a burden-local state transition. Owner and delta labels alone do not Land.",
            "- For `FPD.foreign-premise-detection`, the dereferenced body must expose the foreign/imported premise, imported criterion, hidden criterion, or imported tribunal that was functioning as proof. Owner labels or generic criterion language do not Land.",
            "- Emit standalone public landing lines such as `Land(Bn): ...` or `HOLD(Bn): ...` only after the final Stage 04 body_ref for that burden; `Contribution-to-Land(Bn):` alone is not a landing line.",
            "- Never print `Land(Bn):` for a burden while another assigned or later Stage 04 body_ref for the same burden remains unrendered.",
            "Required submove block skeletons:",
        ]
    )
    landing_lines: list[str] = []
    seen_landing_targets: set[str] = set()
    for ref in assigned_body_refs:
        detail = dict(act_details[ref])
        mirror = owner_details.get(ref, {})
        if isinstance(mirror.get("burden_id"), str) and mirror["burden_id"]:
            detail["burden_id"] = str(mirror["burden_id"])
        burden_id = detail["burden_id"] or canonical_burden_id(ref.split("B", 1)[0] + "B")
        flags = completion_flags.get(ref, {})
        public_burden = public_burden_id(burden_id)
        public_ref = public_submove_id(ref)
        if flags.get("first_for_burden"):
            lines.append(f"- Start burden block: `## Burden {burden_id[1:]} / {public_burden} — <burden-local title>` before {ref}.")
        else:
            lines.append(f"- Continue the existing {public_burden} burden block for {ref}; do not emit a new burden heading.")
        if burden_id and flags.get("last_for_burden") and burden_id not in seen_landing_targets:
            seen_landing_targets.add(burden_id)
            landing_lines.append(
                f"  Land({public_burden}): summarize the cumulative state delta from the visible submove block(s); "
                f"use `HOLD({public_burden}):` instead if the burden is not landed."
            )
        lines.extend(
            [
                f"- {public_ref}[{detail['owner']}] - {detail['operation']} over {detail['pressure']} (mirrors machine body_ref `{ref}`)",
                f"  Target: {detail['pressure']}.",
                f"  Operation: {detail['operation']} must act on {detail['pressure']} with owner family {detail['owner']}.",
                f"  Result/state-change: {detail['delta_result']}; state-change must be visible in local prose.",
                f"  Contribution-to-Land({public_burden}): explain why {detail['delta_result']} licenses Land({public_burden}) because the burden-local AFTER state changed; generic contribution prose is not enough.",
                "  Local proof capsule: make BEFORE, OPERATION, AFTER, DELTA, and LAND-LICENSE recoverable in this block; if the body cannot name the burden-local change, render HOLD/PARTIAL instead of Land.",
                "  TTP Operation Body: expand the local governed operation in ordinary public prose.",
            ]
        )
        family = canonical_delta_owner(detail["owner"]) or str(detail["owner"]).strip().upper()
        if family == "P7":
            lines.append(
                "  Procedure boundary: explicitly name the STOP/HOLD/PARTIAL or bounded-stop condition, "
                "the held/non-load-bearing route boundary, and the reopen condition in this body."
            )
        elif family == "M8":
            if detail["operation"] == "dependency-trace":
                lines.append(
                    "  M8 dependency-trace operation: use the registered operation token `dependency-trace`; "
                    "the operation-specific delta_result must be `dependency-exposed`. State the concrete "
                    "dependency edge or carrier relation, the trace path it exposes, and how exposing that "
                    "dependency changes this burden. Do not use `entailment-blocked` for dependency-trace; "
                    "route consequence or entailment-blocking work to `consequence-trace`, or render "
                    "HOLD/PARTIAL instead of `Land(Bn)`."
                )
            else:
                lines.append(
                    "  M8 consequence-trace operation: use the registered operation token `consequence-trace`; "
                    "assume the live pressure, trace at least one concrete downstream implication or entailment, "
                    "name why that consequence is blocked/demoted/unacceptable in the selected noetic frame, "
                    "and put result words such as dependency-exposed or entailment-bounded in `Result/state-change:`, not `Operation:`. "
                    "A marker-rich row is not enough: if the public body cannot state the consequence/dependency, "
                    "the tested if-accepted implication, and the burden-local state change, render HOLD/PARTIAL "
                    "instead of `Land(Bn)`."
                )
        elif family == "V10":
            lines.append(
                "  V10 provenance/content operation: visibly vet transmission/provenance, content, and authority/status "
                "for this exact source pressure; do not merely cite, summarize, or sort sources without the "
                "V10 transmission/content-authority operation body."
            )
        elif family == "PROOF_METHOD":
            if detail["operation"] == "proof-route-status-audit":
                lines.append(
                    "  Proof-method route-status operation: visibly identify the proof forum, standard of proof, "
                    "tribunal/burden-function, proof eligibility, supporting texts, and premise/inference/conclusion "
                    "scope being assigned to this proof carrier. State the parser-stable local change: `the proof "
                    "route status is clarified because the proof forum, standard of proof, tribunal/burden-function, "
                    "proof eligibility, and premise/inference/conclusion scope are no longer treated as a neutral proof route.`"
                )
            else:
                lines.append(
                    "  Proof-method carrier operation: visibly classify the proof family/carrier, name the premise "
                    "or predicate set being loaded, identify the inference grammar and conclusion scope, and state "
                    "the parser-stable local state change: `the proof carrier is classified as a proof carrier whose "
                    "premise set, inference grammar, and conclusion scope are no longer treated as a neutral proof.`"
                )
        elif family == "PATTERN_PROFILE":
            if detail["operation"] == "proof-packet-reconstruction":
                lines.append(
                    "  Pattern-profile proof-packet operation: reconstruct the proof packet in public order and name "
                    "the hidden source moves, predicate transfers, conclusion jump, forum switch, or carrier compression "
                    "that changed in this burden. State the parser-stable local change: `the proof packet is reconstructed "
                    "so its hidden source moves, predicate transfers, and conclusion jump are exposed.`"
                )
            else:
                lines.append(
                    "  Pattern-profile loaded-label operation: identify the label as a noetic/worldview/identity carrier, "
                    "expose the hidden proof/source/authority rule it transmits, and state that the loaded label carrier "
                    "function is exposed or classified. The `Contribution-to-Land` line must say this licenses Land "
                    "because the label no longer carries motive, source authority, or conclusion force as proof by itself. "
                    "If the body only names the label or owner, render HOLD/PARTIAL instead of Land."
                )
        elif family == "FPD":
            lines.append(
                "  FPD foreign-premise-detection operation: expose the foreign/imported premise, imported criterion, "
                "hidden criterion, imported tribunal, or hidden court that was functioning as proof; name how that "
                "imported premise or criterion changes this burden. If the public body cannot show the imported "
                "premise/criterion, render HOLD/PARTIAL instead of `Land(Bn)`."
            )
        elif family == "DO_ATTRIBUTE":
            lines.append(
                "  Attribute-precision operation: type the person/nature or attribute relation, separate the relevant "
                "levels of predication, name the category confusion or transfer being blocked, and make the "
                "burden-local state change visible before Land."
            )
        elif family == "SOURCE":
            if detail["operation"] == "source-order-repair":
                lines.append(
                    "  SOURCE source-order-repair operation: explicitly order source lineage, quotation "
                    "chain, inherited-claim order, source priority, derivation order, or evidential "
                    "dependency for this exact pressure. Authority/rank/tribunal/source-sovereignty "
                    "prose alone is not source-order proof; use HOLD/PARTIAL or authority-order-repair "
                    "if that is the actual transition."
                )
            elif detail["operation"] == "authority-order-repair":
                lines.append(
                    "  SOURCE authority-order-repair operation: explicitly order authority, rank, "
                    "tribunal, judging office, source-sovereignty, or public-truth authority for this "
                    "exact pressure. Source-lineage/quotation prose alone is not authority-order proof."
                )
            else:
                lines.append(
                    "  SOURCE/source-status operation: explicitly sort source authority, source function, "
                    "proof-stack order, or hidden support for this exact pressure; do not merely say the "
                    "source route was handled. `status` is not a callable ACT operation; use a registered "
                    "SOURCE operation such as `source-order`, `source-order-repair`, `authority-order-repair`, "
                    "or `sort` only when licensed by the copied ACT row."
                )
    if landing_lines:
        lines.extend(["Required standalone landing lines for this ACT slice:", *landing_lines])
    return "\n".join(lines)


def stage07_field_witness_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    act_details = stage04_act_details_by_ref(stage04)
    if not act_details:
        return ""
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    generated_records = stage05_generated_burden_records(stage05)
    generated_burdens = ordered_unique(
        [*stage05_generated_burdens(stage05), *[str(record.get("id") or "") for record in generated_records if record.get("id")]]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    act_owner_routes_by_burden = stage04_owner_routes_by_burden(stage04)
    executed_act_burdens = set(act_owner_routes_by_burden)
    owner_routes_by_burden = dict(act_owner_routes_by_burden)
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    terminal_states = {burden: str(terminal_states.get(burden) or "landed") for burden in b_total}
    generated_record_by_id = {str(record.get("id")): dict(record) for record in generated_records if record.get("id")}
    edges = stage05_dependency_edges(stage05)
    reread_state = stage05.get("reread_state") if isinstance(stage05, dict) else {}
    if not isinstance(reread_state, dict):
        reread_state = {}
    final_source = burden_endpoint_id(reread_state.get("source_burden") or reread_state.get("source")) or (b_total[-1] if b_total else "")
    final_type = str(reread_state.get("route_result_type") or "no_new_resultant").strip().rstrip(".;:,")
    final_route = str(reread_state.get("route") or "STOP").strip().rstrip(".;:,")
    unresolved_burdens = stage05_unresolved_burdens(stage05)
    terminal_states, unresolved_burdens = normalize_stage07_generated_terminal_accounting(
        generated_burdens=generated_burdens,
        generated_record_by_id=generated_record_by_id,
        terminal_states=terminal_states,
        unresolved_burdens=unresolved_burdens,
        executed_act_burdens=executed_act_burdens,
    )
    def unresolved_terminal(burden: str) -> bool:
        return burden in unresolved_burdens or re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            terminal_states.get(burden, ""),
        ) is not None

    held_or_partial_burdens = stage07_held_or_partial_burdens(
        b_total,
        terminal_states,
        unresolved_burdens,
    )
    if (
        held_or_partial_burdens
        and final_type in {"no_new_resultant", "none", "stable", ""}
        and final_route.upper() == "STOP"
    ):
        final_source = held_or_partial_burdens[0]
        final_type = "hold_partial"
        final_route = "HOLD"
    live_registers = stage02_public_live_registers(stage02, burden_floor)
    diagnostic_coverage = stage02_register_coverage(stage02, burden_floor)
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    for edge in edges:
        target = edge["to"]
        if target not in generated_burdens:
            continue
        record = generated_record_by_id.setdefault(
            target,
            {
                "id": target,
                "type": "generated_burden",
                "generation_depth": 1,
                "terminal_state": terminal_states.get(target, "held-with-reason"),
                "activation_state": "generated_unexecuted",
            },
        )
        record.setdefault("generated_by", f"MRP({edge['from']})")
        record.setdefault("reason", f"generated by {edge['from']} -> {target}")
        track = generated_burden_track(record, [edge.get("type", "")])
        if track:
            record.setdefault("track", track)
        raw_route = record.get("required_owner_route")
        tokens: list[str] = []
        if isinstance(raw_route, list):
            tokens.extend(str(item).strip() for item in raw_route if str(item).strip())
        elif isinstance(raw_route, str) and raw_route.strip():
            tokens.append(raw_route.strip())
        if tokens:
            owner_routes_by_burden[target] = ordered_unique([*(owner_routes_by_burden.get(target) or []), *tokens])
    held_terminal_burdens = [
        burden
        for burden, state in terminal_states.items()
        if re.search(r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b", str(state or ""))
    ]
    unresolved_burdens = ordered_unique([*unresolved_burdens, *held_terminal_burdens])
    graph_line, roots, parallel_groups = stage07_dependency_graph_scaffold(b_total, edges)
    closed_terminal_states = {"landed", "cleared", "discharged-as-derivative"}
    coverage_complete = not unresolved_burdens and all(
        str(state).strip() in closed_terminal_states for state in terminal_states.values()
    )
    unresolved_text = ", ".join(unresolved_burdens)
    closure_status = (
        "coverage_complete=true"
        if coverage_complete
        else f"coverage_complete=false; unresolved_burdens=[{unresolved_text}]"
    )
    divergence_status = "neutral" if coverage_complete else f"non-neutral / unresolved_burdens=[{unresolved_text}]"
    generated_unresolved = [burden for burden in unresolved_burdens if burden in generated_burdens]
    b_la_unresolved = [
        burden
        for burden in unresolved_burdens
        if burden in burden_floor and burden not in generated_burdens
    ]
    other_unresolved = [
        burden
        for burden in unresolved_burdens
        if burden not in generated_unresolved and burden not in b_la_unresolved
    ]
    curl_markers: list[str] = []
    if generated_unresolved:
        curl_markers.append(f"generated_burden_hold=[{', '.join(generated_unresolved)}]")
    if b_la_unresolved:
        curl_markers.append(f"b_la_hold_open=[{', '.join(b_la_unresolved)}]")
    if other_unresolved:
        curl_markers.append(f"unresolved_burdens=[{', '.join(other_unresolved)}]")
    curl_status = "null" if coverage_complete else f"unresolved / {'; '.join(curl_markers)}"
    incoming_source_by_target = {edge["to"]: edge["from"] for edge in edges}
    owner_activation_rows: list[dict[str, Any]] = []
    nar_rows: list[dict[str, Any]] = []
    for ref, detail in act_details.items():
        target = detail["burden_id"]
        route_type = stage07_route_type_for_burden(target, edges, final_source, final_type)
        incoming_source = incoming_source_by_target.get(target)
        source = target if target in roots or not incoming_source else f"MRP({incoming_source})"
        if target in generated_burdens:
            generated_source = str(generated_record_by_id.get(target, {}).get("generated_by") or "")
            if generated_source:
                source = generated_source
        owner_activation_row = {
            "body_ref": ref,
            "source": source,
            "target": target,
            "owner": detail["owner"],
            "owner_id": detail["owner"],
            "operation": detail["operation"],
            "pressure": detail["pressure"],
            "delta": f"{detail['delta']}:{detail['delta_result']}",
            "delta_result": detail["delta_result"],
            "land": detail["land"],
            "land_target": target,
            "terminal_state": terminal_states.get(target, "landed"),
            "mrp_route_result_type": route_type,
            "ordering_role": "required",
        }
        raw_delta = str(detail["delta"])
        if "κ" in raw_delta or "kappa" in raw_delta.lower():
            owner_activation_row.update(
                {
                    "kappa_carrier": f"κ dependency-radius carrier for {ref} over {detail['pressure']}",
                    "dependency_radius": f"{target} dependency radius after {detail['operation']}",
                    "reread_state_effect": f"R(H,Delta) binds Δκ back to {target} before release",
                }
            )
        owner_activation_rows.append(owner_activation_row)
        nar_rows.append(
            {
                "burden_id": target,
                "owner_id": detail["owner"],
                "operation": detail["operation"],
                "delta_result": detail["delta_result"],
                "mrp_route_result_type": route_type,
                "terminal_state": terminal_states.get(target, "landed"),
                "generation_depth": 0 if target in burden_floor else 1,
            }
        )
    for burden in generated_burdens:
        if any(row.get("burden_id") == burden for row in nar_rows):
            continue
        record = generated_record_by_id.get(burden, {})
        route_type = stage07_route_type_for_burden(burden, edges, final_source, final_type)
        nar_rows.append(
            {
                "burden_id": burden,
                "owner_id": "MRP",
                "operation": route_type or "generated-burden-instantiation",
                "delta_result": str(record.get("reason") or terminal_states.get(burden) or "generated burden held"),
                "mrp_route_result_type": route_type,
                "terminal_state": terminal_states.get(burden, "held-with-reason"),
                "generation_depth": int(record.get("generation_depth") or 1),
            }
        )
    owner_activation_ordering = {
        "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
        "required_before": [],
        "parallel_groups": [],
    }
    rows_by_target: dict[str, list[dict[str, Any]]] = {}
    for row in owner_activation_rows:
        rows_by_target.setdefault(str(row.get("target") or ""), []).append(row)
    for target, rows in rows_by_target.items():
        if len(rows) <= 1:
            continue
        for before, after in zip(rows, rows[1:]):
            before_owner = str(before.get("owner") or "").strip()
            after_owner = str(after.get("owner") or "").strip()
            before_operation = str(before.get("operation") or "").strip()
            after_operation = str(after.get("operation") or "").strip()
            if not before_owner or not after_owner:
                continue
            before_ordering_owner = ordering_owner_family(before_owner)
            after_ordering_owner = ordering_owner_family(after_owner)
            if before_ordering_owner != after_ordering_owner:
                owner_activation_ordering["required_before"].append(
                    {
                        "target": target,
                        "before_owner": before_owner,
                        "after_owner": after_owner,
                    }
                )
            elif before_operation and after_operation and before_operation != after_operation:
                owner_activation_ordering["required_before"].append(
                    {
                        "target": target,
                        "before_owner": before_owner,
                        "before_operation": before_operation,
                        "before_body_ref": str(before.get("body_ref") or "").strip(),
                        "after_owner": after_owner,
                        "after_operation": after_operation,
                        "after_body_ref": str(after.get("body_ref") or "").strip(),
                    }
                )
            elif before_operation and after_operation and before_operation == after_operation:
                owner_activation_ordering["required_before"].append(
                    {
                        "target": target,
                        "before_owner": before_owner,
                        "before_operation": before_operation,
                        "before_body_ref": str(before.get("body_ref") or "").strip(),
                        "after_owner": after_owner,
                        "after_operation": after_operation,
                        "after_body_ref": str(after.get("body_ref") or "").strip(),
                    }
                )
    per_burden_entries = stage05_per_burden_entries(stage05)
    mrp_resultants = mrp_resultant_rows_from_entries(per_burden_entries)
    formal_reread_states = stage07_formal_reread_states(
        per_burden_entries,
        terminal_states,
        unresolved_burdens=unresolved_burdens,
        owner_routes_by_burden=owner_routes_by_burden,
    )

    def terminal_state_line(burden: str) -> str:
        state = terminal_states.get(burden, "landed")
        if burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            source = str(record.get("generated_by") or "MRP(source)")
            reason = str(record.get("reason") or "generated burden is held at this Stage 07 boundary")
            if burden in executed_act_burdens:
                return (
                    f"{public_burden_id(burden)}: {state} / {public_graph_value(source)} / "
                    f"visible Stage 04 ACT rows / {reason}"
                )
            return f"{public_burden_id(burden)}: {state} / {public_graph_value(source)} / no Stage 04 ACT rows / {reason}"
        return f"{public_burden_id(burden)}: {state} / ACT owners / landed by visible owner activations"

    visible_lines = [
        f"Initial burden set: [{public_burden_list(burden_floor)}]",
        f"𝔅_LA (B_LA) = {public_burden_set(burden_floor)}",
        f"𝔅_MRP (B_MRP) = {public_burden_set(generated_burdens)}",
        f"𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {public_burden_set(b_total)}",
        "Burden dependency graph:",
        public_graph_line(b_total, edges),
        "Terminal states:",
        *[terminal_state_line(burden) for burden in b_total],
        "Owner activations:",
        *[detail["row"] for detail in act_details.values()],
        "MRP resultants:",
        *[
            f"MRP({public_burden_id(row['source'])}): type={row['type']}; finding={row['finding']}; graph={public_graph_value(row['graph'])}; route={row['route']}"
            for row in mrp_resultants
        ],
        "Formal reread states:",
        *[
            f"formal_reread_state({row['source_burden']}): reread={row['reread']}; type={row['route_result_type']}; graph={row['graph_delta']}; route={row['route']}"
            for row in formal_reread_states
        ],
        f"∇·B: {divergence_status} / runtime execution field remains bounded to the displayed handoff",
        f"∇×κ: {curl_status} / runtime execution field remains bounded to the displayed handoff",
        f"𝒞(Ψᴺ): {'COMPLETE' if coverage_complete else 'HOLD'} / {closure_status}; runtime execution field remains bounded to the displayed handoff",
        "T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake",
    ]
    nodes_payload: list[dict[str, Any]] = []
    for burden in b_total:
        node: dict[str, Any] = {
            "id": burden,
            "type": "generated_burden" if burden in generated_burdens else "burden",
            "register_types": burden_registers.get(burden, []),
            "state": terminal_states.get(burden, "landed"),
            "generation_depth": 1 if burden in generated_burdens else 0,
        }
        if burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            if record.get("generated_by"):
                node["generated_by"] = record["generated_by"]
            node["track"] = generated_burden_track(record)
        nodes_payload.append(node)
    generated_payload = [generated_record_by_id[burden] for burden in generated_burdens if burden in generated_record_by_id]
    scaffold = {
        "B_LA": burden_floor,
        "B_MRP": generated_burdens,
        "B_total": b_total,
        "nodes": nodes_payload,
        "edges": edges,
        "generated_burdens": generated_payload,
        "mrp_resultants": mrp_resultants,
        "formal_reread_states": formal_reread_states,
        "field_diagnostics": {"divergence_check": divergence_status, "curl_check": curl_status},
        "terminal_states": terminal_states,
        "closure": {"status": closure_status, "unresolved_burdens": unresolved_burdens},
        "T_lang": "T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake",
        "owner_activation_ordering": owner_activation_ordering,
        "owner_activations": owner_activation_rows,
        "normalized_activation_record": {
            "n_frame": str((stage02 or {}).get("selected_n_frame") or (stage06 or {}).get("selected_n_frame") or "selected-n-frame"),
            "live_registers": live_registers,
            "burden_floor": burden_floor,
            "per_burden": nar_rows,
        },
        "coverage_proof": {
            "initial_burden_set": burden_floor,
            "terminal_states": terminal_states,
            "dependency_graph": {
                "nodes": b_total,
                "edges": [{"from": edge["from"], "to": edge["to"]} for edge in edges],
                "roots": roots,
                "parallel_groups": parallel_groups,
                "acyclic": True,
            },
            "diagnostic_completeness": {
                "live_registers": live_registers,
                "coverage": diagnostic_coverage,
                "complete": True,
            },
            "divergence_check": divergence_status,
            "curl_check": curl_status,
            "max_generation_depth": 1 if generated_burdens else 0,
            "coverage_complete": coverage_complete,
        },
    }
    lines = [
        "",
        "Stage 07 field_witness mirror contract:",
        "- After Closing Formulation, print the visible Closure/Reconstruction Witness ledger, then emit the `field_witness` JSON as the final machine payload using these exact line shapes:",
        *[f"  {line}" for line in visible_lines],
        "- If Stage 05 `generated_burdens` is empty, `𝔅_MRP (B_MRP)` is empty: visible `𝔅_MRP (B_MRP) = {}` and JSON `\"B_MRP\": []`; never place baseline Layer-A burdens in `B_MRP`.",
        "- Visible public burden IDs must use superscript notation such as `¹B`; JSON machine IDs remain canonical ASCII such as `B1`.",
        "- `𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required in the visible ledger; JSON `B_total` must equal JSON `B_LA` plus `B_MRP` in order.",
        "- `coverage_proof.dependency_graph` is required with `nodes`, `edges`, `roots`, and boolean `acyclic`.",
        "- `coverage_proof.diagnostic_completeness.live_registers` and `normalized_activation_record.live_registers` must include every Layer A live register, including `kappa` when Layer A makes it load-bearing. If a Layer A register is non-load-bearing or held, state that explicitly instead of omitting it from the mirrors.",
        "- If the dependency edge list is empty and `B_total` has multiple nodes, the visible graph line must declare every node as a parallel root, for example `¹B (root) || ²B (root)`, and JSON `parallel_groups` must mirror the full node group.",
        "- If the dependency edge list is non-empty, the visible graph must declare every root node plus every actual edge, for example `¹B (root); ²B (root); ⁴B → ⁵B`; never convert an edgeful graph into `¹B (root) → ⁵B` unless Stage 05 actually records that edge.",
        "- A generated `B_MRP` burden must appear in `generated_burdens[]`, `nodes[]`, `B_total`, `terminal_states`, `coverage_proof.dependency_graph.nodes`, and `normalized_activation_record.per_burden[]` with `generation_depth`, `track`, and `generated_by` provenance.",
        "- If Stage 05 leaves `unresolved_burdens`, any terminal state is `held-with-reason`, `carried-PARTIAL`, `carried-RECURSE`, or otherwise HOLD/PARTIAL, or `no_new_resultant_proof.proved=false`, do not claim `coverage_complete=true`; set `coverage_complete` false and keep the burden held/unresolved instead of synthesizing terminal STOP proof.",
        "- Do not synthesize a generated-burden `MRP(Bn)` row with `graph=none`; visible generated/held MRP resultants must expose the concrete Stage 05 graph edge such as `⁴B → ⁵B`, while JSON mirrors keep ASCII machine IDs.",
        "- Each `nodes[]` burden payload must include `register_types` copied from Stage 02 `burden_floor_details` when live registers are present.",
        "- Every `owner_activations[]` object must include both `target` and `land_target`; the checker reads `target` for terminal-state evidence.",
        "- `field_witness.owner_activation_ordering` must be an object with `policy_id=\"diagnostic-ir-pressure-owner-floor-v1\"`; an `owner_activations[]` list or prose ordering explanation is not a deterministic ordering plan.",
        "- If multiple load-bearing `owner_activations[]` rows land the same target, set each row's `ordering_role` and add `owner_activation_ordering.required_before[]` edges that mirror Stage 04 / visible ACT order. If the same owner lands multiple operations on the same target, every required-before edge for that pair must include `before_operation`, `after_operation`, `before_body_ref`, and `after_body_ref`; owner-only self-edges do not prove operation order, and repeated same-owner-operation rows need body_ref endpoints. For genuinely parallel owner work, set every involved row to `ordering_role=\"parallel\"`, give them a stable `ordering_group`, and mirror that group in `owner_activation_ordering.parallel_groups[]`; same-owner parallel operations must be listed in `parallel_groups[].members[]` with `owner` and `operation`.",
        "- Emit one `normalized_activation_record.per_burden[]` row per `owner_activations[]` mirror, plus one MRP-owned row for each generated `B_MRP` burden that has no Stage 04 ACT rows; do not collapse these into one summary row per burden.",
        "- Each NAR row must include `burden_id`, `owner_id`, `operation`, `delta_result`, `mrp_route_result_type`, `terminal_state`, and integer `generation_depth`.",
        "- `formal_reread_states[]` is required; emit exactly one row for every `mrp_resultants[]` source and keep `source_burden`, `route_result_type`, `graph_delta`, and `route` aligned with that MRP row.",
        "- The visible public MRP source set, Closure/Reconstruction Witness `MRP(...)` rows, JSON `mrp_resultants[]`, and JSON `formal_reread_states[]` must be exactly the same source set. If a public `MRP(G)` source is not in the scaffold, remove it or convert it to non-load-bearing held-route prose; do not leave an unmatched visible MRP block.",
        "- `curl_state` values must be parser-stable JSON strings. When curl is absent/resolved, emit JSON string `\"null\"`, never bare JSON null.",
        "- Terminal `STOP` / `no_new_resultant` rows must set `reread` to `R(H,Delta)`, `divergence_state` to `neutral`, `curl_state` to JSON string `\"null\"`, `graph_delta` to `none`, omit `next_burden`, and include `no_new_resultant_proof.escape_routes_checked` as a JSON list.",
        "- Complete closure must have no HOLD/PARTIAL formal rows and no held terminal burdens. If a terminal `STOP` / `no_new_resultant` row is only a bounded MRP row for a generated or unresolved burden, keep `coverage_complete=false`, set `no_new_resultant_proof.proved=false`, and keep explicit HOLD/PARTIAL accounting instead of claiming clean closure.",
        "- Treat the visible Closure/Reconstruction Witness, machine `field_witness` JSON, NAR rows, and optional sidecars as separate clone states that must mirror the same ACT/body_ref chain; do not let prose or sidecar custody substitute for the machine witness.",
        "- The line `field_witness` is only a marker. It must be followed by a parseable JSON object containing the checker-owned witness, including `normalized_activation_record`; YAML, prose, or a heading-only witness is invalid.",
        "- `body_ref` remains the bare join key copied from ACT. Public submove headings, owner labels, operations, register axes, deltas, and graph proof text must not be encoded into `body_ref`.",
        "- `land` and `land_target` are witness mirrors of visible `Land(Bn)` clauses; every owner activation must copy the same target burden rather than summarizing closure in prose.",
        "- For every `owner_activations[]` mirror, `owner` must contain only the ACT owner token or owner family, not `owner.operation`.",
        "- Put the operation in the separate `operation` field, and keep `owner_id` aligned with the owner token.",
        "- Do not set `owner` to `owner.operation`; for example use `\"owner\": \"FPD\"` and `\"operation\": \"foreign-premise-detection\"`.",
        "- Do not add unscaffolded `owner_activations[]` rows. Every row must correspond to exactly one Stage 04 ACT `body_ref` shown in the mirror scaffold below; generated MRP-only rows belong in `normalized_activation_record.per_burden[]`, not `owner_activations[]`.",
        "- For every `owner_activations[]` mirror whose `delta` carrier is `Δκ` / `Delta-kappa`, include explicit `kappa_carrier`, `dependency_radius`, and `reread_state_effect` fields. Those fields must mention kappa/dependency/R(H,Delta) evidence that binds the dependency-radius transition back to the raw burden target before release.",
        "- Required field_witness scaffold and checker-owned keys (copy field names exactly; adapt prose details but keep the structure):",
        json.dumps(scaffold, ensure_ascii=False, indent=2),
        "- Mirror these exact ACT-visible values by body_ref; include `target` exactly as shown:",
    ]
    for ref, detail in act_details.items():
        mirror_row = {
            "body_ref": ref,
            "owner": detail["owner"],
            "owner_id": detail["owner"],
            "operation": detail["operation"],
            "pressure": detail["pressure"],
            "delta": f"{detail['delta']}:{detail['delta_result']}",
            "delta_result": detail["delta_result"],
            "land": detail["land"],
            "target": detail["burden_id"],
            "land_target": detail["burden_id"],
            "ordering_role": "required",
        }
        raw_delta = str(detail["delta"])
        if "κ" in raw_delta or "kappa" in raw_delta.lower():
            mirror_row.update(
                {
                    "kappa_carrier": f"κ dependency-radius carrier for {ref} over {detail['pressure']}",
                    "dependency_radius": f"{detail['burden_id']} dependency radius after {detail['operation']}",
                    "reread_state_effect": f"R(H,Delta) binds Δκ back to {detail['burden_id']} before release",
                }
            )
        lines.append(
            "  "
            + json.dumps(mirror_row, ensure_ascii=False)
        )
    return "\n".join(lines)


def first_json_object_from_text(text: str) -> dict[str, Any] | None:
    cursor = 0
    decoder = json.JSONDecoder()
    while True:
        start = text.find("{", cursor)
        if start < 0:
            return None
        try:
            decoded, _end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        return decoded if isinstance(decoded, dict) else None


def contract_scaffold_lines(contract: str, marker: str) -> list[str]:
    lines = contract.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        if not collecting:
            if marker in line:
                collecting = True
            continue
        if line.startswith("  "):
            collected.append(line[2:])
            continue
        if collected and line.startswith("- "):
            break
    return collected


def stage07_mrp_reread_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    contract = stage07_mrp_reread_contract_guidance(previous_stages)
    lines = contract_scaffold_lines(contract, "ledger-only: print the reconstruction floor")
    if not lines:
        return ""
    return "\n".join(lines).rstrip() + "\n"


def stage07_field_witness_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    contract = stage07_field_witness_contract_guidance(previous_stages)
    visible_lines = contract_scaffold_lines(
        contract,
        "print the visible Closure/Reconstruction Witness ledger",
    )
    if not visible_lines:
        return ""
    scaffold_tail = contract.split("Required field_witness scaffold", 1)[-1]
    payload = first_json_object_from_text(scaffold_tail)
    if payload is None:
        return ""
    return (
        "Closure/Reconstruction Witness\n"
        + "\n".join(visible_lines).rstrip()
        + "\n\nfield_witness\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n"
    )


RESTORATIVE_SLOT_PATTERNS = (
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Restored criterion/(?:order|orientation)\s*:\s*\S"),
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Relieved pressure\s*:\s*\S"),
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Held/scoped/reopenable remainder\s*:\s*\S"),
)
CONCEALMENT_MODE_LINE_RE = re.compile(r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?Concealment mode\s*:\s*)(?P<value>.*)$")
CONCEALMENT_COMPONENT_TOKEN_RE = re.compile(
    r"(?i)\b(?:iʿrāḍ|i'rad|i`rad|irad|juḥūd|juhud|inkār|inkar|istikbār|istikbar|nifāq|nifaq)\b"
)
PUBLIC_SUBMOVE_HEADING_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?"
    r"(?P<ref>(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B[1-9][0-9]*)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.][1-9][0-9]*))"
    r"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\]"
)
OPERATION_LINE_RE = re.compile(r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?Operation\s*:\s*)(?P<body>.*)$")
RESULT_STATE_LINE_RE = re.compile(r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?Result(?:/state-change)?\s*:\s*)(?P<body>.*)$")
CONTRIBUTION_LAND_LINE_RE = re.compile(
    r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?Contribution-to-Land\((?P<land>[^)]*)\)\s*:\s*)(?P<body>.*)$"
)
CHECKER_STABLE_STATE_RE = re.compile(
    r"(?i)\b(?:state change|classified|exposed|separated|bounded|no longer treated as a neutral proof|"
    r"typed as a proof carrier|carrier function is exposed)\b"
)
CHECKER_STABLE_CONTRIBUTION_RE = re.compile(
    r"(?i)\b(?:because|so that|therefore|thereby|rather than|instead of|licenses?|lands?|"
    r"contributes? to|prevents?|blocks?|preserves?|keeps?|separates?|bars?|routes?|state change|"
    r"delta|no longer|can no longer|cannot|establish(?:es|ed)?|shows?)\b"
)
PROOF_METHOD_BODY_BACKED_RE = re.compile(
    r"(?is)\bproof\b.*\b(?:premise|predicate|definition)\b.*\b(?:infer|deriv|logic tree)\w*\b.*"
    r"\b(?:conclusion|contradiction|scope)\b"
)
PROOF_ROUTE_STATUS_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:proof forum|standard of proof|burden[- ]function|burden role|"
    r"tribunal[- ]function|proof eligibility|supporting texts?|premise/inference/conclusion scope)\b"
)
PATTERN_PROFILE_BODY_BACKED_RE = re.compile(
    r"(?is)\blabel\b.*\bcarrier\b.*\b(?:hidden|transmit\w*|proof rule|source|authority|worldview|noetic)\b.*"
    r"\b(?:loaded|compress\w*|carrier function)\b"
)
PATTERN_PROFILE_PROOF_PACKET_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:proof[- ]packet|logic[- ]tree|mind[- ]map|diagram)\b.*"
    r"\b(?:reconstruct|reconstructed|rebuilding|rebuilt|ordered sequence|sequence of transfers)\b.*"
    r"\b(?:source moves?|predicate transfers?|conclusion jump|forum switch|carrier compression|load[- ]bearing assumptions)\b"
)
FPD_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:foreign premise|imported premise|imported criterion|hidden criterion|"
    r"foreign criterion|unargued criterion|criterion import|premise import|"
    r"imported tribunal|imported court|hidden court)\b"
)
SOURCE_AUTHORITY_ORDER_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:authority|rank|tribunal|judging office|higher court|source[- ]sovereignty|"
    r"source authority|public[- ]truth authority|approval standard)\b.*"
    r"\b(?:order|ordered|sort|sorted|rank|tribunal|court|sovereignty|authority)\b"
)
SOURCE_SOURCE_ORDER_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:source lineage|quotation chain|quotation order|inherited[- ]claim order|"
    r"inherited claim|source priority|source precedence|evidential dependency|"
    r"derivation order|source chain|testimony source|report source)\b"
)
DO_ATTRIBUTE_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:attribute[- ]precision|person/nature|person[- ]nature|attribute|predicate|"
    r"category confusion|category transfer|cruelty|kindness|generosity|typed|typing)\b"
)
DO_ATTRIBUTE_TRANSITION_BACKED_RE = re.compile(
    r"(?is)\b(?:types?|typed|typing|separates?|separated|blocking?|blocked|bounded|"
    r"classifies?|classified|category transfer|category confusion|predicate level)\b"
)
DO_SECOND_LOOP_BODY_BACKED_RE = re.compile(
    r"(?is)\b(?:accountability|hujjah|ḥujjah|warning|knowledge|capacity|record|culpability|"
    r"guidance|coercion|persuasion|punishment|proportionality|mercy|justice|judge)\b"
)
DO_SECOND_LOOP_TRANSITION_BACKED_RE = re.compile(
    r"(?is)\b(?:narrows?|narrowed|bounds?|bounded|calibrates?|calibrated|separates?|"
    r"separated|blocks?|blocked|sequences?|sequenced|no longer)\b"
)
SECTION_ROLE_HEADING_PATTERNS = {
    "restorative_response": re.compile(
        r"(?i)^\s*(?:#{1,6}\s*)?(?:(?:\*\*|__|\*|_)\s*)?"
        r"Restorative Response"
        r"(?:\s*(?:\*\*|__|\*|_))?\s*(?:#+\s*)?$"
    ),
    "closing_formulation": re.compile(
        r"(?i)^\s*(?:#{1,6}\s*)?(?:(?:\*\*|__|\*|_)\s*)?"
        r"Closing Formulation"
        r"(?:\s*(?:\*\*|__|\*|_))?\s*(?:#+\s*)?$"
    ),
}


def ttp_operation_body_from_public_block(block: str) -> str:
    match = re.search(r"(?ims)^\s*(?:[-*]\s*)?TTP Operation Body\s*:\s*(?P<body>.*)$", block)
    return match.group("body") if match else ""


def concealment_source_components(value: str) -> list[str]:
    aliases = {
        "iʿrāḍ": "irad",
        "i'rad": "irad",
        "i`rad": "irad",
        "irad": "irad",
        "juḥūd": "juhud",
        "juhud": "juhud",
        "inkār": "inkar",
        "inkar": "inkar",
        "istikbār": "istikbar",
        "istikbar": "istikbar",
        "nifāq": "nifaq",
        "nifaq": "nifaq",
    }
    return ordered_unique(
        aliases.get(match.group(0).lower(), match.group(0).lower())
        for match in CONCEALMENT_COMPONENT_TOKEN_RE.finditer(value)
    )


def restorative_response_slots_present(text: str) -> bool:
    return all(pattern.search(text) for pattern in RESTORATIVE_SLOT_PATTERNS)


def demote_duplicate_own_section_heading(
    section_role: str,
    text: str,
) -> tuple[str, dict[str, Any] | None]:
    pattern = SECTION_ROLE_HEADING_PATTERNS.get(section_role)
    if pattern is None:
        return text, None
    lines = text.splitlines(keepends=True)
    seen_heading = False
    demoted = 0
    retained: list[str] = []
    for line in lines:
        if pattern.match(line.strip()):
            if seen_heading:
                demoted += 1
                continue
            seen_heading = True
        retained.append(line)
    if demoted == 0:
        return text, None
    normalized = "".join(retained)
    if text.endswith("\n") and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized, {
        "role": section_role,
        "demoted_duplicate_own_section_headings": demoted,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(normalized.encode("utf-8")),
    }


def canonicalize_mixed_concealment_projection(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    if section_role not in {"visible_opening", "layer_a_diagnostic_ir"}:
        return text, None
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    expected_line = next(
        (
            line
            for line in stage07_layer_a_diagnostic_state_lines(stage02)
            if line.lower().startswith("concealment mode:")
        ),
        "",
    )
    expected_value = expected_line.split(":", 1)[1].strip() if ":" in expected_line else ""
    if "mixed" not in expected_value.lower() or len(concealment_source_components(expected_value)) < 2:
        return text, None

    replacements = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal replacements
        value = match.group("value")
        if "mixed" in value.lower() and len(concealment_source_components(value)) < 2:
            replacements += 1
            return f"{match.group('prefix')}{expected_value}"
        return match.group(0)

    normalized = CONCEALMENT_MODE_LINE_RE.sub(replace_match, text)
    if replacements == 0 and section_role == "layer_a_diagnostic_ir" and not CONCEALMENT_MODE_LINE_RE.search(text):
        insertion = expected_line + "\n"
        header = re.search(r"(?im)^\s*(?:#{1,6}\s*)?.*\b(?:Layer A|Diagnostic IR|DSL/IR)\b.*$", normalized)
        if header:
            insert_at = normalized.find("\n", header.end())
            if insert_at >= 0:
                normalized = normalized[: insert_at + 1] + insertion + normalized[insert_at + 1 :]
            else:
                normalized = normalized.rstrip() + "\n" + insertion
        else:
            normalized = insertion + normalized.lstrip()
        replacements = 1
    if replacements == 0:
        return text, None
    return normalized, {
        "role": section_role,
        "canonicalized_mixed_concealment_projection": True,
        "source_components": concealment_source_components(expected_value),
        "replacement_count": replacements,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(normalized.encode("utf-8")),
    }


def body_ref_to_public_ref(value: str) -> str:
    return public_submove_id(str(value or "").strip())


def layer_b_submove_blocks(text: str) -> list[tuple[re.Match[str], int, str]]:
    matches = list(PUBLIC_SUBMOVE_HEADING_RE.finditer(text))
    blocks: list[tuple[re.Match[str], int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match, end, text[match.start() : end]))
    return blocks


def owner_transition_body_backed(detail: dict[str, str], block: str) -> bool:
    owner = str(detail.get("owner") or "").strip()
    operation = str(detail.get("operation") or "").strip()
    family = canonical_delta_owner(owner) or owner
    operation_body = ttp_operation_body_from_public_block(block)
    if owner == "proof-method-audit" and operation == "proof-family-and-carrier-audit":
        return bool(PROOF_METHOD_BODY_BACKED_RE.search(operation_body))
    if owner == "proof-method-audit" and operation == "proof-route-status-audit":
        return bool(
            PROOF_METHOD_BODY_BACKED_RE.search(operation_body)
            and PROOF_ROUTE_STATUS_BODY_BACKED_RE.search(operation_body)
        )
    if owner == "pattern-profiling" and operation == "loaded-label-carrier-audit":
        return bool(PATTERN_PROFILE_BODY_BACKED_RE.search(operation_body))
    if owner == "pattern-profiling" and operation == "proof-packet-reconstruction":
        return bool(PATTERN_PROFILE_PROOF_PACKET_BODY_BACKED_RE.search(operation_body))
    if family == "FPD" and operation == "foreign-premise-detection":
        return bool(FPD_BODY_BACKED_RE.search(operation_body))
    if family == "SOURCE" and operation == "authority-order-repair":
        return bool(SOURCE_AUTHORITY_ORDER_BODY_BACKED_RE.search(operation_body))
    if family == "SOURCE" and operation == "source-order-repair":
        return bool(SOURCE_SOURCE_ORDER_BODY_BACKED_RE.search(operation_body))
    if family == "DO_ATTRIBUTE" and operation == "attribute-precision":
        return bool(
            DO_ATTRIBUTE_BODY_BACKED_RE.search(operation_body)
            and DO_ATTRIBUTE_TRANSITION_BACKED_RE.search(operation_body)
        )
    if family == "DO_SECOND_LOOP":
        return bool(
            DO_SECOND_LOOP_BODY_BACKED_RE.search(operation_body)
            and DO_SECOND_LOOP_TRANSITION_BACKED_RE.search(operation_body)
        )
    return False


def state_change_sentence_for_owner_transition(detail: dict[str, str]) -> str:
    owner = str(detail.get("owner") or "").strip()
    operation = str(detail.get("operation") or "").strip()
    family = canonical_delta_owner(owner) or owner
    if owner == "proof-method-audit" and operation == "proof-family-and-carrier-audit":
        return (
            " State change: the proof carrier is classified as a proof carrier whose "
            "premise set, inference grammar, and conclusion scope are no longer treated "
            "as a neutral proof."
        )
    if owner == "proof-method-audit" and operation == "proof-route-status-audit":
        return (
            " State change: the proof route status is clarified because the proof forum, "
            "standard of proof, tribunal/burden-function, proof eligibility, supporting texts, "
            "and premise/inference/conclusion scope are no longer treated as a neutral proof route."
        )
    if owner == "pattern-profiling" and operation == "loaded-label-carrier-audit":
        return (
            " State change: the loaded label carrier function is exposed and classified, "
            "so the carrier no longer transports the conclusion as a premise."
        )
    if owner == "pattern-profiling" and operation == "proof-packet-reconstruction":
        return (
            " State change: the proof packet is reconstructed so its hidden source moves, "
            "predicate transfers, and conclusion jump are exposed rather than carried invisibly."
        )
    if family == "FPD" and operation == "foreign-premise-detection":
        return (
            " State change: the foreign premise and imported criterion are exposed, "
            "so the hidden criterion or imported tribunal no longer travels as neutral proof."
        )
    if family == "SOURCE" and operation == "authority-order-repair":
        return (
            " State change: authority-order-repaired; the authority/rank/tribunal relation "
            "is ordered, so rival source authority no longer functions as a higher court "
            "or external tribunal over revelation."
        )
    if family == "SOURCE" and operation == "source-order-repair":
        return (
            " State change: source-order-repaired; the source lineage, source priority, "
            "and evidential dependency are explicitly ordered, so the inherited claim no "
            "longer travels as an unworked source chain."
        )
    if family == "DO_ATTRIBUTE" and operation == "attribute-precision":
        return (
            " State change: the attribute-precision operation types the attribute or predicate relation, "
            "separates the relevant levels, and blocks the category transfer from carrying the burden."
        )
    if family == "DO_SECOND_LOOP" and operation == "accountability-hujjah-compression":
        return (
            " State change: the hujjah/accountability compression is narrowed through warning, knowledge, "
            "capacity, record, and response sequencing, so bare non-belief no longer carries the burden."
        )
    if family == "DO_SECOND_LOOP" and operation == "coercive-guidance-demand":
        return (
            " State change: guidance, warning, persuasion, and coercion are separated, so the demand for "
            "compelling disclosure no longer carries the burden."
        )
    if family == "DO_SECOND_LOOP" and operation == "fitrah-ayat-baseline":
        return (
            " State change: the fitrah/ayat baseline is established as a guidance-order route, so the "
            "burden is no longer carried by a bare neutrality claim."
        )
    if family == "DO_SECOND_LOOP" and operation == "punishment-proportionality-accountability":
        return (
            " State change: punishment proportionality is calibrated through accountability, warning, "
            "knowledge, capacity, record, and the Judge's right, so raw affective magnitude no longer "
            "carries the burden."
        )
    return ""


def operation_sentence_for_owner_transition(detail: dict[str, str]) -> str:
    owner = str(detail.get("owner") or "").strip()
    operation = str(detail.get("operation") or "").strip()
    family = canonical_delta_owner(owner) or owner
    if family == "FPD" and operation == "foreign-premise-detection":
        return (
            "foreign-premise-detection: expose the foreign premise and imported criterion "
            "functioning as proof for this burden."
        )
    return ""


def land_license_sentence_for_owner_transition(detail: dict[str, str], public_burden: str) -> str:
    owner = str(detail.get("owner") or "").strip()
    operation = str(detail.get("operation") or "").strip()
    family = canonical_delta_owner(owner) or owner
    land_target = public_burden.strip() or public_burden_id(str(detail.get("burden_id") or "B1"))
    if owner == "proof-method-audit" and operation == "proof-family-and-carrier-audit":
        return (
            f"This licenses Land({land_target}) because the proof carrier's premise set, "
            "inference grammar, and conclusion scope are exposed, so the carrier no longer "
            "functions as neutral proof by itself."
        )
    if owner == "proof-method-audit" and operation == "proof-route-status-audit":
        return (
            f"This licenses Land({land_target}) because the proof forum, standard of proof, "
            "tribunal/burden-function, proof eligibility, and premise/inference/conclusion scope "
            "are bounded, so the route no longer functions as neutral proof by itself."
        )
    if owner == "pattern-profiling" and operation == "loaded-label-carrier-audit":
        return (
            f"This licenses Land({land_target}) because the loaded label carrier function is exposed "
            "and classified, so the label no longer carries motive, source authority, or conclusion "
            "force as proof by itself."
        )
    if owner == "pattern-profiling" and operation == "proof-packet-reconstruction":
        return (
            f"This licenses Land({land_target}) because the proof packet is reconstructed with its "
            "hidden source moves, predicate transfers, and conclusion jump exposed, so the packet "
            "no longer carries closure invisibly."
        )
    if family == "FPD" and operation == "foreign-premise-detection":
        return (
            f"This licenses Land({land_target}) because the foreign premise and imported criterion "
            "are exposed, so the hidden criterion no longer travels as neutral proof."
        )
    if family == "SOURCE" and operation == "authority-order-repair":
        return (
            f"This licenses Land({land_target}) because the authority/rank/tribunal relation is "
            "ordered, so rival source authority no longer functions as a higher court or external "
            "tribunal over revelation."
        )
    if family == "SOURCE" and operation == "source-order-repair":
        return (
            f"This licenses Land({land_target}) because the source lineage, source priority, and "
            "evidential dependency are explicitly ordered, so the inherited claim no longer travels "
            "as an unworked source chain."
        )
    if family == "DO_ATTRIBUTE" and operation == "attribute-precision":
        return (
            f"This licenses Land({land_target}) because attribute precision types the attribute or "
            "predicate relation, separates the relevant levels, and blocks the category transfer from "
            "carrying proof force."
        )
    if family == "DO_SECOND_LOOP" and operation == "accountability-hujjah-compression":
        return (
            f"This licenses Land({land_target}) because the hujjah/accountability compression is "
            "narrowed through warning, knowledge, capacity, record, and response sequencing."
        )
    if family == "DO_SECOND_LOOP" and operation == "coercive-guidance-demand":
        return (
            f"This licenses Land({land_target}) because guidance, warning, persuasion, and coercion "
            "are separated, so coercive-disclosure pressure is bounded."
        )
    if family == "DO_SECOND_LOOP" and operation == "fitrah-ayat-baseline":
        return (
            f"This licenses Land({land_target}) because the fitrah/ayat baseline is established as "
            "guidance-order evidence rather than a bare neutrality claim."
        )
    if family == "DO_SECOND_LOOP" and operation == "punishment-proportionality-accountability":
        return (
            f"This licenses Land({land_target}) because punishment proportionality is calibrated "
            "through accountability, warning, knowledge, capacity, record, and the Judge's right."
        )
    return ""


def checker_stable_state_for_owner_transition(detail: dict[str, str], body: str) -> bool:
    family = canonical_delta_owner(str(detail.get("owner") or "").strip()) or str(detail.get("owner") or "").strip()
    if family in {"DO_ATTRIBUTE", "DO_SECOND_LOOP", "SOURCE"}:
        sentence = state_change_sentence_for_owner_transition(detail).strip()
        return bool(sentence and sentence in body)
    return bool(CHECKER_STABLE_STATE_RE.search(body))


def checker_stable_contribution_for_owner_transition(detail: dict[str, str], body: str) -> bool:
    family = canonical_delta_owner(str(detail.get("owner") or "").strip()) or str(detail.get("owner") or "").strip()
    if family in {"DO_ATTRIBUTE", "DO_SECOND_LOOP", "SOURCE"}:
        land_target = str(detail.get("burden_id") or "").strip()
        public_land = public_burden_id(land_target) if land_target else ""
        license_sentence = land_license_sentence_for_owner_transition(detail, public_land)
        return bool(license_sentence and license_sentence in body)
    return bool(CHECKER_STABLE_CONTRIBUTION_RE.search(body))


def canonicalize_layer_b_owner_transition_facets(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    if section_role != "layer_b_act":
        return text, None
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    act_details = stage04_act_details_by_ref(stage04)
    if not act_details:
        return text, None
    details_by_public_ref = {
        body_ref_to_public_ref(ref): detail
        for ref, detail in act_details.items()
        if (
            str(detail.get("owner") or "").strip() in {"proof-method-audit", "pattern-profiling"}
            and str(detail.get("operation") or "").strip()
            in {
                "proof-family-and-carrier-audit",
                "proof-route-status-audit",
                "loaded-label-carrier-audit",
                "proof-packet-reconstruction",
            }
        )
        or (
            (canonical_delta_owner(str(detail.get("owner") or "").strip()) or "")
            == "FPD"
            and str(detail.get("operation") or "").strip() == "foreign-premise-detection"
        )
        or (
            (canonical_delta_owner(str(detail.get("owner") or "").strip()) or "")
            == "SOURCE"
            and str(detail.get("operation") or "").strip()
            in {"authority-order-repair", "source-order-repair"}
        )
        or (
            (canonical_delta_owner(str(detail.get("owner") or "").strip()) or "")
            == "DO_ATTRIBUTE"
            and str(detail.get("operation") or "").strip() == "attribute-precision"
        )
        or (
            (canonical_delta_owner(str(detail.get("owner") or "").strip()) or "")
            == "DO_SECOND_LOOP"
            and str(detail.get("operation") or "").strip()
            in {
                "accountability-hujjah-compression",
                "coercive-guidance-demand",
                "fitrah-ayat-baseline",
                "punishment-proportionality-accountability",
            }
        )
    }
    if not details_by_public_ref:
        return text, None

    replacements: list[dict[str, str]] = []
    chunks: list[str] = []
    cursor = 0
    for match, block_end, block in layer_b_submove_blocks(text):
        public_ref = match.group("ref")
        detail = details_by_public_ref.get(public_ref)
        if not detail or not owner_transition_body_backed(detail, block):
            continue
        sentence = state_change_sentence_for_owner_transition(detail)
        if not sentence:
            continue
        operation_sentence = operation_sentence_for_owner_transition(detail)
        operation_line_changed = False

        def replace_operation_line(operation_match: re.Match[str]) -> str:
            nonlocal operation_line_changed
            if not operation_sentence:
                return operation_match.group(0)
            body = operation_match.group("body").strip()
            if operation_sentence in body:
                return operation_match.group(0)
            operation_line_changed = True
            return f"{operation_match.group('prefix')}{operation_sentence}"

        def replace_result_line(result_match: re.Match[str]) -> str:
            body = result_match.group("body").rstrip()
            if checker_stable_state_for_owner_transition(detail, body):
                return result_match.group(0)
            return f"{result_match.group('prefix')}{body.rstrip('.')}." + sentence

        normalized_block, _operation_replacement_count = OPERATION_LINE_RE.subn(
            replace_operation_line,
            block,
            count=1,
        )
        normalized_block, result_replacement_count = RESULT_STATE_LINE_RE.subn(
            replace_result_line,
            normalized_block,
            count=1,
        )
        land_license_changed = False

        def replace_contribution_line(contribution_match: re.Match[str]) -> str:
            nonlocal land_license_changed
            body = contribution_match.group("body").strip()
            if checker_stable_contribution_for_owner_transition(detail, body):
                return contribution_match.group(0)
            public_burden = contribution_match.group("land").strip()
            land_license = land_license_sentence_for_owner_transition(detail, public_burden)
            if not land_license:
                return contribution_match.group(0)
            land_license_changed = True
            return f"{contribution_match.group('prefix')}{land_license}"

        normalized_block = CONTRIBUTION_LAND_LINE_RE.sub(
            replace_contribution_line,
            normalized_block,
            count=1,
        )
        if (
            not operation_line_changed
            and result_replacement_count <= 0
            and not land_license_changed
        ) or normalized_block == block:
            continue
        chunks.append(text[cursor : match.start()])
        chunks.append(normalized_block)
        cursor = block_end
        replacements.append(
            {
                "body_ref": str(detail.get("body_ref") or ""),
                "owner": str(detail.get("owner") or ""),
                "operation": str(detail.get("operation") or ""),
                "delta_result": str(detail.get("delta_result") or ""),
            }
        )
    if not replacements:
        return text, None
    chunks.append(text[cursor:])
    normalized = "".join(chunks)
    return normalized, {
        "role": section_role,
        "canonicalized_owner_transition_facets": True,
        "facet_replacements": replacements,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(normalized.encode("utf-8")),
    }


def stage07_restorative_response_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage05, "B_LA")
    generated_burdens = stage05_generated_burdens(stage05)
    unresolved_burdens = list_field(stage05, "unresolved_burdens")
    if not unresolved_burdens and isinstance(stage05, dict):
        proof = stage05.get("no_new_resultant_proof")
        if isinstance(proof, dict):
            unresolved_burdens = [
                b_id(item) for item in proof.get("unresolved_burdens", []) if b_id(item)
            ]
    held = ordered_unique([*generated_burdens, *unresolved_burdens])
    floor_text = public_burden_list(burden_floor) if burden_floor else "the displayed baseline burden floor"
    held_text = public_burden_list(held) if held else "future concrete burdens only"
    if held:
        remainder = (
            f"Generated or unresolved burden(s) {held_text} remain held/scoped/reopenable "
            "unless a later bounded pass actually executes matching ACT rows; "
            "coverage_complete=false stays honest for this closure boundary."
        )
    else:
        remainder = (
            "Specific future objections remain reopenable only as concrete named burdens; "
            "no hidden proof-carousel or total-system demand is allowed to repair the landed reply."
        )
    return (
        "Restorative Response\n\n"
        f"Restored criterion/order: Preserve the landed source-owned burden order {floor_text} "
        "and return the field to tawhid, fitrah, and sound reason without letting a later model "
        "override the local proof state.\n\n"
        "Relieved pressure: The visible ACT and MRP rows block the reply's local premise, "
        "source-order, proof-stack, analogy, source-status, and consequence pressure from "
        "governing the answer before the visible burden order is worked.\n\n"
        f"Held/scoped/reopenable remainder: {remainder}\n"
    )


def stage07_closing_formulation_budget_supplement(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    burden_floor = (
        list_field(stage02, "burden_floor")
        or list_field(stage06, "B_LA")
        or list_field(stage05, "B_LA")
    )
    generated_burdens = ordered_unique(
        [
            *stage05_generated_burdens(stage05),
            *list_field(stage06, "B_MRP"),
        ]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    unresolved_burdens = ordered_unique(
        [
            *stage05_unresolved_burdens(stage05),
            *list_field(stage06, "unresolved_burdens"),
        ]
    )
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    generated_records = {
        str(record.get("id")): dict(record)
        for record in stage05_generated_burden_records(stage05)
        if record.get("id")
    }
    terminal_states = {burden: str(terminal_states.get(burden) or "landed") for burden in b_total}
    terminal_states, unresolved_burdens = normalize_stage07_generated_terminal_accounting(
        generated_burdens=generated_burdens,
        generated_record_by_id=generated_records,
        terminal_states=terminal_states,
        unresolved_burdens=unresolved_burdens,
        executed_act_burdens=set(stage04_owner_routes_by_burden(stage04)),
    )
    n_frame = ""
    if isinstance(stage02, dict):
        n_frame = str(stage02.get("selected_n_frame") or "")
    if not n_frame and isinstance(stage06, dict):
        n_frame = str(stage06.get("selected_n_frame") or "")
    if not n_frame:
        n_frame = "the selected noetic frame"

    lines = [
        "### Closure boundary confirmation",
        "",
        f"The final close remains tied to {n_frame}. It does not ask the reader to accept a total-system verdict before the displayed burdens have done their work. It keeps the reply's pressure ordered by the visible burden floor, the landed ACT rows, the MRP reread, and the held remainder.",
        "",
        "The closing therefore has three controlled claims. First, the stated reply fails only at the burden actually worked by the visible owner rows. Second, the repair is local to the argument actually made: source wording or report status, analogy, proof-stack backread, inference pressure, and source-order pressure. Third, anything not executed as an ACT row remains reopenable as a named burden rather than being smuggled into a clean global close.",
        "",
        "### Burden-state recap",
        "",
    ]
    if not b_total:
        lines.append("The displayed burden ledger remains the governing scope of this close.")
    for burden in b_total:
        public_burden = public_burden_id(burden)
        state = str(terminal_states.get(burden) or ("generated-held" if burden in generated_burdens else "landed"))
        registers = ", ".join(burden_registers.get(burden, [])) or "local registers"
        if burden in generated_burdens:
            record = generated_records.get(burden, {})
            generated_by = str(record.get("generated_by") or f"MRP({burden})")
            lines.append(
                f"- {public_burden}: generated by {public_graph_value(generated_by)}; state={state}; registers={registers}. "
                "It is not counted as a baseline floor burden unless a later pass actually executes matching ACT rows."
            )
        else:
            lines.append(
                f"- {public_burden}: baseline burden; state={state}; registers={registers}. "
                "Its local close is limited to the visible owner operation and its public Land(...) consequence."
            )
    held_text = public_burden_list(unresolved_burdens) if unresolved_burdens else "none"
    lines.extend(
        [
            "",
            "### Reopenable remainder",
            "",
            f"The remaining live or generated burden set is {held_text}. When that set is non-empty, the close is intentionally a HOLD/PARTIAL close for that remainder. When it is empty, the close still remains bounded to concrete future burdens rather than to an unlimited proof-carousel.",
            "",
            "This matters for the reader because the answer should not win by compression. The reply is answered where its stated moves actually operate: the cited wording or report status, the source-order relation, the category mistake in the analogy, the secondary status of proof-stack backreads, and the difference between worked evidence and hidden support.",
            "",
            "The final formulation is therefore deliberately disciplined. It restores the order of the verse, names the burden that remains open if a further answer wants to continue, and refuses to convert a bounded refutation into an unbounded claim that every possible downstream doctrine has been exhausted.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def stage07_restorative_response_budget_supplement(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    burden_floor = (
        list_field(stage02, "burden_floor")
        or list_field(stage04, "act_burdens")
        or list_field(stage06, "B_LA")
        or list_field(stage05, "B_LA")
    )
    generated_records = {
        str(record.get("id")): dict(record)
        for record in stage05_generated_burden_records(stage05)
        if record.get("id")
    }
    generated_burdens = ordered_unique(
        [
            *stage05_generated_burdens(stage05),
            *[burden for burden in generated_records if burden],
            *list_field(stage06, "B_MRP"),
        ]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    unresolved_burdens = ordered_unique(
        [
            *stage05_unresolved_burdens(stage05),
            *list_field(stage06, "unresolved_burdens"),
        ]
    )
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    terminal_states = {burden: str(terminal_states.get(burden) or "landed") for burden in b_total}
    terminal_states, unresolved_burdens = normalize_stage07_generated_terminal_accounting(
        generated_burdens=generated_burdens,
        generated_record_by_id=generated_records,
        terminal_states=terminal_states,
        unresolved_burdens=unresolved_burdens,
        executed_act_burdens=set(stage04_owner_routes_by_burden(stage04)),
    )
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    lines = [
        "### Restorative reconstruction floor",
        "",
        "The restorative response stays tied to the selected noetic structure, the selected owner family, and the burden route that actually landed. It does not add catalogue mass merely because more TTPs are callable, and it does not hide a remaining generated burden behind smooth pastoral prose.",
        "",
        "### Restored burden order",
        "",
    ]
    if not b_total:
        lines.append("The visible burden ledger remains the scope of the restoration.")
    for burden in b_total:
        public_burden = public_burden_id(burden)
        registers = ", ".join(burden_registers.get(burden, [])) or "local registers"
        state = terminal_states.get(burden, "landed")
        if burden in generated_burdens:
            record = generated_records.get(burden, {})
            generated_by = str(record.get("generated_by") or "MRP(selected-parent)")
            if burden in unresolved_burdens or "hold" in state.lower() or "partial" in state.lower() or "recurse" in state.lower():
                lines.append(
                    f"- {public_burden}: generated by {public_graph_value(generated_by)}; registers={registers}; state={state}. Restoration keeps this pressure visible as HOLD/PARTIAL/RECURSE until selected ACT evidence executes it."
                )
            else:
                lines.append(
                    f"- {public_burden}: generated by {public_graph_value(generated_by)}; registers={registers}; state={state}. Restoration may treat it as landed only because visible execution evidence has already landed it."
                )
        else:
            lines.append(
                f"- {public_burden}: baseline burden; registers={registers}; state={state}. Restoration follows after its visible ACT submoves, Land(...), and R(H,Δ) consequence rather than replacing them."
            )
    held_text = public_burden_list(unresolved_burdens) if unresolved_burdens else "none"
    lines.extend(
        [
            "",
            "### Relieved pressure",
            "",
            "The restored field relieves only the pressure that the visible owner rows worked: criterion, source-order, proof-stack, predication, method, analogy, or restoration pressure named by the selected route. A later objection remains admissible only as a concrete burden with its own owner route.",
            "",
            "### Held/scoped/reopenable remainder",
            "",
            f"The remaining generated or unresolved burden set is {held_text}. When that set is non-empty, restoration is intentionally partial for that remainder and coverage_complete=false stays honest. When it is empty, restoration still stays bounded to the worked burden floor rather than claiming a total-system answer.",
            "",
            "### Fitrah and sound-reason return",
            "",
            "The public close returns the reader to tawhid, fitrah, and sound reason by naming the repaired criterion and the scoped reopen condition. It must be warm enough to restore orientation, but strict enough that comfort prose cannot turn held pressure into fake closure.",
            "",
            "The restoration should therefore tell the reader what changed in the field: which burden no longer governs, which criterion has been restored, which owner result made that restoration licensed, and which pressure remains outside the close. That is reader-facing care and proof discipline at the same time.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def stage07_mrp_reread_budget_supplement(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    burden_floor = (
        list_field(stage02, "burden_floor")
        or list_field(stage04, "act_burdens")
        or list_field(stage04, "act_targets")
        or list_field(stage06, "B_LA")
    )
    generated_records = {
        str(record.get("id")): dict(record)
        for record in stage05_generated_burden_records(stage05)
        if record.get("id")
    }
    generated_burdens = ordered_unique(
        [
            *stage05_generated_burdens(stage05),
            *[burden for burden in generated_records if burden],
            *list_field(stage06, "B_MRP"),
        ]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    terminal_states = {burden: str(terminal_states.get(burden) or "landed") for burden in b_total}
    unresolved_burdens = ordered_unique(
        [
            *stage05_unresolved_burdens(stage05),
            *list_field(stage06, "unresolved_burdens"),
        ]
    )
    terminal_states, unresolved_burdens = normalize_stage07_generated_terminal_accounting(
        generated_burdens=generated_burdens,
        generated_record_by_id=generated_records,
        terminal_states=terminal_states,
        unresolved_burdens=unresolved_burdens,
        executed_act_burdens=set(stage04_owner_routes_by_burden(stage04)),
    )
    n_frame = ""
    if isinstance(stage02, dict):
        n_frame = str(stage02.get("selected_n_frame") or "")
    if not n_frame and isinstance(stage06, dict):
        n_frame = str(stage06.get("selected_n_frame") or "")
    if not n_frame:
        n_frame = "the selected noetic structure"

    lines = [
        "### MRP terminal reconstruction floor",
        "",
        f"The reread remains bounded to {n_frame}, the selected burden route, and the matched owner/TTP floor. It does not add burden mass from catalogue presence alone, and it does not erase live pressure merely to make a terminal row look complete.",
        "",
        "### Route-state ledger",
        "",
    ]
    if not b_total:
        lines.append("No concrete burden ledger was available beyond the selected route record.")
    for burden in b_total:
        public_burden = public_burden_id(burden)
        state = str(terminal_states.get(burden) or "landed")
        if burden in generated_burdens:
            record = generated_records.get(burden, {})
            generated_by = str(record.get("generated_by") or "MRP(selected-parent)")
            route = "HOLD/PARTIAL/RECURSE" if burden in unresolved_burdens else "executed/landed only if ACT evidence exists"
            lines.append(
                f"- {public_burden}: generated by {public_graph_value(generated_by)}; state={state}; route={route}. "
                "It is not a baseline 𝔅_LA burden unless the selected Layer A floor actually contained it."
            )
        else:
            lines.append(
                f"- {public_burden}: baseline 𝔅_LA burden; state={state}; route bounded by its visible ACT and R(H,Δ) evidence."
            )
    held_text = public_burden_list(unresolved_burdens) if unresolved_burdens else "none"
    generated_text = public_burden_set(generated_burdens)
    lines.extend(
        [
            "",
            "### Stop/Hold boundary",
            "",
            f"𝔅_MRP (B_MRP) = {generated_text}. Unresolved or generated-held burdens: {held_text}.",
            "A STOP/no_new_resultant row is clean only when the visible MRP block, terminal_states, formal_reread_states, coverage_proof, and Closure/Reconstruction Witness all agree that no generated or held burden remains live.",
            "When a generated burden is merely present but not selected for ACT execution, it stays inert or held; when it is selected but not executed, the honest route is HOLD/PARTIAL/RECURSE rather than fake Land(B).",
            "",
            "### Catalogue availability boundary",
            "",
            "Callable owner/TTP availability is not activation. The reread may consult the selected callable catalogue after Land(B), but a catalogue entry adds no ACT row, no owner activation, and no burden node unless live pressure licenses that selected route.",
            "If a selected owner body is unavailable, the route remains a named HOLD/PARTIAL boundary with OWNER-BODY-NOT-LOADED evidence rather than a landed proof claim.",
            "",
            "### Reconstruction agreement",
            "",
            "The public MRP block, visible terminal ledger, formal_reread_states row, generated_burdens provenance, dependency graph, and coverage proof must reconstruct the same selected route. If any one of those mirrors remains open, the terminal section must keep the open state visible instead of compressing it into global closure.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def compiled_section_budget_guardrail(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
    section_min_bytes: int,
) -> tuple[str, dict[str, Any] | None]:
    if section_min_bytes <= 0 or len(text.encode("utf-8")) >= section_min_bytes:
        return text, None
    supplement = ""
    marker = ""
    if section_role == "closing_formulation":
        marker = "### Closure boundary confirmation"
        supplement = stage07_closing_formulation_budget_supplement(previous_stages)
    elif section_role == "mrp_reread_terminal":
        marker = "### MRP terminal reconstruction floor"
        supplement = stage07_mrp_reread_budget_supplement(previous_stages)
    elif section_role == "restorative_response":
        marker = "### Restorative reconstruction floor"
        supplement = stage07_restorative_response_budget_supplement(previous_stages)
    if not marker or marker in text:
        return text, None
    if not supplement:
        return text, None
    supplemented = text.rstrip() + "\n\n" + supplement
    return supplemented, {
        "role": section_role,
        "compiled_section_budget_guardrail": True,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(supplemented.encode("utf-8")),
        "section_min_bytes": section_min_bytes,
    }


def canonicalize_visible_act_rows_from_stage04(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    if section_role != "layer_b_act" or "⟦ACT" not in text:
        return text, None
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    act_details = stage04_act_details_by_ref(stage04)
    if not act_details:
        return text, None
    replacements: list[dict[str, str]] = []
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if "⟦ACT" not in line:
            lines.append(line)
            continue
        ref_match = ACT_BODY_REF_RE.search(line)
        if ref_match is None:
            lines.append(line)
            continue
        body_ref = ref_match.group(1)
        canonical = act_details.get(body_ref)
        if canonical is None:
            lines.append(line)
            continue
        canonical_row = str(canonical.get("row") or "")
        if not canonical_row or line.strip() == canonical_row:
            lines.append(line)
            continue
        newline = "\n" if line.endswith("\n") else ""
        lines.append(canonical_row + newline)
        replacements.append({"body_ref": body_ref})
    if not replacements:
        return text, None
    normalized = "".join(lines)
    return normalized, {
        "role": section_role,
        "canonicalized_visible_act_rows_from_stage04": True,
        "replacement_count": len(replacements),
        "body_refs": [item["body_ref"] for item in replacements],
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(normalized.encode("utf-8")),
    }


def canonical_compiled_structural_section(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    text, mixed_concealment_event = canonicalize_mixed_concealment_projection(
        section_role,
        text,
        previous_stages,
    )
    text, visible_act_event = canonicalize_visible_act_rows_from_stage04(
        section_role,
        text,
        previous_stages,
    )
    text, owner_transition_event = canonicalize_layer_b_owner_transition_facets(
        section_role,
        text,
        previous_stages,
    )
    text, public_alias_event = canonicalize_public_burden_aliases(section_role, text)
    text, duplicate_heading_event = demote_duplicate_own_section_heading(section_role, text)
    if section_role == "mrp_reread_terminal":
        scaffold = stage07_mrp_reread_section_scaffold(previous_stages)
    elif section_role == "field_witness_nar":
        scaffold = stage07_field_witness_section_scaffold(previous_stages)
    elif section_role == "restorative_response":
        if restorative_response_slots_present(text):
            event = public_alias_event or duplicate_heading_event
            if event is not None and public_alias_event is not None and event is not public_alias_event:
                event["canonicalized_public_burden_aliases"] = True
                event["public_alias_replacement_count"] = public_alias_event["replacement_count"]
            if event is not None and duplicate_heading_event is not None and event is not duplicate_heading_event:
                event["demoted_duplicate_own_section_headings"] = duplicate_heading_event[
                    "demoted_duplicate_own_section_headings"
                ]
            if event is not None and visible_act_event is not None and event is not visible_act_event:
                event["canonicalized_visible_act_rows_from_stage04"] = True
                event["visible_act_row_replacement_count"] = visible_act_event["replacement_count"]
            return text, event
        scaffold = stage07_restorative_response_section_scaffold(previous_stages)
        body = re.sub(
            r"(?is)^\s*(?:#{1,6}\s*)?Restorative Response\s*",
            "",
            text,
            count=1,
        ).lstrip()
        if body:
            scaffold = scaffold.rstrip() + "\n\n" + body.rstrip() + "\n"
    else:
        event = (
            public_alias_event
            or owner_transition_event
            or mixed_concealment_event
            or duplicate_heading_event
            or visible_act_event
        )
        if event is not None and public_alias_event is not None and event is not public_alias_event:
            event["canonicalized_public_burden_aliases"] = True
            event["public_alias_replacement_count"] = public_alias_event["replacement_count"]
        if event is not None and duplicate_heading_event is not None and event is not duplicate_heading_event:
            event["demoted_duplicate_own_section_headings"] = duplicate_heading_event[
                "demoted_duplicate_own_section_headings"
            ]
        if event is not None and visible_act_event is not None and event is not visible_act_event:
            event["canonicalized_visible_act_rows_from_stage04"] = True
            event["visible_act_row_replacement_count"] = visible_act_event["replacement_count"]
        return text, event
    if not scaffold:
        return text, mixed_concealment_event or duplicate_heading_event
    if text.strip() == scaffold.strip():
        return text, mixed_concealment_event or duplicate_heading_event
    event = {
        "role": section_role,
        "canonicalized_structural_stage07_section": True,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(scaffold.encode("utf-8")),
    }
    if mixed_concealment_event is not None:
        event["canonicalized_mixed_concealment_projection"] = True
        event["mixed_concealment_source_components"] = mixed_concealment_event["source_components"]
        event["mixed_concealment_replacement_count"] = mixed_concealment_event["replacement_count"]
    if public_alias_event is not None:
        event["canonicalized_public_burden_aliases"] = True
        event["public_alias_replacement_count"] = public_alias_event["replacement_count"]
    if duplicate_heading_event is not None:
        event["demoted_duplicate_own_section_headings"] = duplicate_heading_event[
            "demoted_duplicate_own_section_headings"
        ]
        event["original_bytes_before_heading_demote"] = duplicate_heading_event["original_bytes"]
    return scaffold, event


def stage05_closed_terminal_state(value: Any) -> bool:
    return str(value or "").strip() in {"landed", "cleared", "discharged-as-derivative"}


def stage05_edge_endpoints(edge: Any) -> tuple[str, str, str]:
    if not isinstance(edge, dict):
        return "", "", ""
    source = burden_endpoint_id(edge.get("from") or edge.get("source"))
    target = burden_endpoint_id(edge.get("to") or edge.get("target"))
    edge_type = str(edge.get("type") or "").strip()
    return source, target, edge_type


def stage05_entry_graph_target(
    entry: dict[str, Any],
    edge_targets_by_source: dict[str, str],
) -> str:
    source = b_id(entry.get("burden_id"))
    if not source:
        return ""
    target = b_id(entry.get("next_burden"))
    if target:
        return target
    graph_target = stage07_route_target_from_graph(entry.get("graph_delta"))
    if graph_target:
        return graph_target
    graph_target = stage07_route_target_from_graph(entry.get("mrp_resultant"))
    if graph_target:
        return graph_target
    return edge_targets_by_source.get(source, "")


def normalize_stage05_initial_burden_continuations(
    stage04: dict[str, Any] | None,
    stage05: dict[str, Any] | None,
) -> None:
    """Map intermediate local STOP rows onto the existing held-burden RECURSE shape."""
    if not isinstance(stage04, dict) or not isinstance(stage05, dict):
        return
    terminal_states = stage05.get("terminal_states")
    entries = stage05.get("per_burden_reread")
    if (
        not isinstance(terminal_states, dict)
        or not isinstance(entries, list)
        or not all(isinstance(entry, dict) for entry in entries)
    ):
        return
    burden_order = ordered_unique(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
    burden_order = [burden for burden in burden_order if burden in terminal_states]
    if len(burden_order) <= 1:
        return
    owner_routes = stage04_owner_routes_by_burden(stage04)
    entry_by_burden = {
        str(entry.get("burden_id") or ""): entry
        for entry in entries
        if isinstance(entry.get("burden_id"), str)
    }
    edges = stage05.get("dependency_graph_edges")
    if not isinstance(edges, list):
        return
    edge_keys = {
        (source, target, edge_type or "held_burden_activation")
        for source, target, edge_type in (stage05_edge_endpoints(edge) for edge in edges)
        if source and target
    }
    edge_targets_by_source = {
        source: target
        for source, target, edge_type in (stage05_edge_endpoints(edge) for edge in edges)
        if source and target and (edge_type or "held_burden_activation") == "held_burden_activation"
    }
    matched_route_hydrations: list[dict[str, str]] = []
    for entry in entries:
        source = b_id(entry.get("burden_id"))
        if not source or str(entry.get("route_result_type") or "") != "held_burden_activation":
            continue
        if str(entry.get("matched_route") or "").strip():
            continue
        target = stage05_entry_graph_target(entry, edge_targets_by_source)
        route_tokens = owner_routes.get(target) or []
        if not target or not route_tokens:
            continue
        entry["matched_route"] = matched_owner_route_line(route_tokens)
        matched_route_hydrations.append(
            {
                "source_burden": source,
                "next_burden": target,
                "matched_route": entry["matched_route"],
            }
        )
    rewrites: list[dict[str, str]] = []
    for source, target in zip(burden_order, burden_order[1:]):
        entry = entry_by_burden.get(source)
        if entry is None:
            continue
        if not stage05_closed_terminal_state(terminal_states.get(source)):
            continue
        if (
            str(entry.get("finding") or "") != "stable"
            or str(entry.get("route_result_type") or "") != "no_new_resultant"
            or str(entry.get("route") or "") != "STOP"
            or str(entry.get("graph_delta") or "") != "none"
            or str(entry.get("preemption_basis") or "") != "none"
        ):
            continue
        public_source = public_burden_id(source)
        public_target = public_burden_id(target)
        rewrites.append(
            {
                "source_burden": source,
                "next_burden": target,
                "raw_route_result_type": "no_new_resultant",
                "canonical_route_result_type": "held_burden_activation",
            }
        )
        entry["reread"] = (
            f"R(H,Δ): held routes rechecked: {public_target}; live remainder: "
            f"{public_target} remains as the next already-routed initial burden; "
            f"release/next: RECURSE to {public_target}."
        )
        entry["route_gradient"] = (
            f"already-held {public_target} from the initial burden set remains live "
            f"after R(H,Δ) from {public_source}."
        )
        entry["finding"] = "genuine-dependent"
        entry["route_result_type"] = "held_burden_activation"
        entry["mrp_resultant"] = f"genuine-dependent -> graph {source} -> {target}; RECURSE"
        entry["graph_delta"] = f"{source} -> {target}"
        entry["preemption_basis"] = "graph-bound"
        entry["route"] = "RECURSE"
        route_tokens = owner_routes.get(target) or []
        if route_tokens:
            entry["matched_route"] = matched_owner_route_line(route_tokens)
        activations = entry.get("pressure_activations")
        if isinstance(activations, dict):
            activations["dependency-tug"] = (
                f"pressure class: dependency-scan — {public_target} remains the next "
                f"already-routed initial burden after {public_source}."
            )
            activations["entailment-pressure"] = (
                f"M8 — route consequence points from {public_source} to {public_target} "
                "without generating a new burden."
            )
        edge_key = (source, target, "held_burden_activation")
        if edge_key not in edge_keys:
            edges.append({"from": source, "to": target, "type": "held_burden_activation"})
            edge_keys.add(edge_key)
    if not rewrites:
        if matched_route_hydrations:
            normalization = normalization_object(stage05)
            normalization["matched_route_hydrations"] = matched_route_hydrations
            stage05["normalization"] = normalization
        return
    proof = stage05.get("no_new_resultant_proof")
    if isinstance(proof, dict) and proof.get("proved") is True:
        proof["basis"] = (
            "No generated B_MRP burden was produced; intermediate original B_LA "
            "continuations are recorded separately as held_burden_activation graph "
            "edges until the final terminal burden."
        )
    normalization = normalization_object(stage05)
    normalization["per_burden_intermediate_stop_continuations"] = rewrites
    if matched_route_hydrations:
        normalization["matched_route_hydrations"] = matched_route_hydrations
    stage05["normalization"] = normalization
    per_burden_errors = staged_output.per_burden_reread_entry_errors(
        entries,
        label="stage-05 per_burden_reread",
        terminal_state_ids=set(str(key) for key in terminal_states),
    )
    if per_burden_errors:
        raise HarnessError(
            "stage-05 per_burden continuation normalization produced invalid records:\n- "
            + "\n- ".join(per_burden_errors)
        )


def validate_incremental_handoffs(stages: list[dict[str, Any]]) -> None:
    stage02 = stage_by_id(stages, "stage-02-layer-a-diagnostic-ir")
    stage03 = stage_by_id(stages, "stage-03-routing-owner-gate")
    stage04 = stage_by_id(stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(stages, "stage-06-field-witness-nar")
    if stage04 and stage05:
        normalize_stage05_initial_burden_continuations(stage04, stage05)
    if stage02 and stage03:
        if set(list_field(stage02, "burden_floor")) != set(list_field(stage03, "route_targets")):
            raise HarnessError("stage-03 route_targets must match stage-02 burden_floor")
    if stage03 and stage04:
        route_targets = set(list_field(stage03, "route_targets"))
        act_targets = set(list_field(stage04, "act_targets"))
        held_targets = stage04_held_target_burdens(stage04)
        extra_act_targets = sorted(act_targets - route_targets)
        if extra_act_targets:
            raise HarnessError(f"stage-04 act_targets not routed by stage-03: {extra_act_targets}")
        missing_route_targets = sorted(route_targets - act_targets - held_targets)
        if missing_route_targets:
            raise HarnessError(
                "stage-04 route_targets must be covered by act_targets or held_act_targets: "
                f"{missing_route_targets}"
            )
    if stage04 and stage06:
        if list_field(stage04, "act_body_refs") != list_field(stage06, "field_witness_body_refs"):
            raise HarnessError("stage-06 field_witness_body_refs must match stage-04 act_body_refs")
        act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
        nar_burdens = set(list_field(stage06, "nar_burdens"))
        missing = sorted(act_burdens - nar_burdens)
        if missing:
            raise HarnessError(f"stage-06 nar_burdens missing ACT burden(s): {missing}")
        owner_activations = list_field(stage06, "owner_activations")
        if owner_activations != list_field(stage06, "field_witness_body_refs"):
            raise HarnessError("stage-06 owner_activations must mirror field_witness_body_refs")
    if stage05 and stage06:
        terminal_states = stage05.get("terminal_states")
        if isinstance(terminal_states, dict):
            missing = sorted(set(terminal_states) - set(list_field(stage06, "nar_burdens")))
            if missing:
                raise HarnessError(f"stage-06 nar_burdens missing terminal-state burden(s): {missing}")
        validate_stage06_nar_route_types_against_stage05(stage05, stage06)
    if stage05 and stage05.get("terminal_states") in ({}, None):
        raise HarnessError("stage-05 terminal_states must be non-empty")
    if stage04 and stage05:
        terminal_states = stage05.get("terminal_states")
        if not isinstance(terminal_states, dict):
            raise HarnessError("stage-05 terminal_states must be a non-empty object")
        act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
        missing = sorted(act_burdens - set(terminal_states))
        if missing:
            raise HarnessError(f"stage-05 terminal_states missing ACT burden(s): {missing}")
        if not isinstance(stage05.get("dependency_graph_edges"), list):
            raise HarnessError("stage-05 dependency_graph_edges must be a list")
        proof = stage05.get("no_new_resultant_proof")
        unresolved = stage05.get("unresolved_burdens") or []
        if proof is True and unresolved:
            raise HarnessError("stage-05 no_new_resultant_proof true conflicts with unresolved_burdens")
        if isinstance(proof, dict) and proof.get("proved") is True and proof.get("unresolved_burdens"):
            raise HarnessError("stage-05 no_new_resultant_proof proved=true conflicts with unresolved_burdens")


def split_route_owner_operation(owner: str) -> tuple[str, str]:
    token = str(owner or "").strip().strip("[]")
    if not token:
        return "", ""
    if canonical_delta_owner(token):
        return token, ""
    if "." in token:
        owner_part, operation_part = token.split(".", 1)
        if owner_part.strip() and operation_part.strip():
            return owner_part.strip(), operation_part.strip()
    return token, ""


def stage03_owner_operation_guidance() -> str:
    lines = [
        "",
        "Stage 03 controlled owner-operation vocabulary:",
        "- If an `owner_routes[]` row is executable, its `operation` / "
        "`owner_operation` value must be one of the listed owner-local callable "
        "operation tokens for that owner family.",
        "- Keep route pressure, source/authority labels, proof pressure, and "
        "delta/result labels out of `operation`; if a route names pressure but "
        "not a callable operation, emit HOLD/PARTIAL instead of inventing an "
        "operation token.",
        "- Source, authority, rank, tribunal, quotation, lineage, or source-order "
        "pressure belongs to SOURCE-family operations when selected; do not "
        "encode that pressure as an M1-P operation.",
        "- Split SOURCE formal repairs by hidden transition state: use "
        "`authority-order-repair` for authority, rank, tribunal, judging-office, "
        "source-sovereignty, public-truth-gate, or source-demotion pressure; use "
        "`source-order-repair` only for source lineage, quotation chain, "
        "inherited-claim order, source priority, derivation order, or evidential "
        "dependency pressure. Do not let authority/tribunal prose pass as "
        "`source-order-repair`.",
        "- M1-P is the performative self-refutation family. Its callable "
        "operations are `test` and `performative-test`; do not mint "
        "`authority-premise-test`, `authority-test`, or similar mixed "
        "source/authority operation labels.",
        "- In Stage 03 `owner_routes[].owner_id`, delta/register family codes "
        "are observations, not executable owner ids. Use the callable owner id "
        "shown below; keep the family code only in classification/detail fields.",
        "- SOURCE is the source/authority delta/register family, not the executable "
        "owner_id. For authority/rank/tribunal/source-sovereignty transitions, use "
        "`owner_id=authority-order-repair` with `operation=authority-order-repair`. "
        "For source-lineage/quotation/inherited-claim/evidential-dependency transitions, "
        "use `owner_id=source-status-repair` with `operation=source-order-repair`.",
    ]
    for family, execution_owner in sorted(FAMILY_EXECUTION_OWNER_IDS.items()):
        lines.append(
            f"- Stage 03 owner_id mapping: `{family}` -> `{execution_owner}`; "
            f"use `{execution_owner}` in `owner_routes[].owner_id`, not `{family}`."
        )
    for family in sorted(OWNER_OPERATION_VOCABULARY):
        operations = ", ".join(sorted(OWNER_OPERATION_VOCABULARY[family]))
        lines.append(f"- {family} operations: {operations}")
    return "\n".join(lines)


def stage04_delta_vocabulary_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage03 = stage_by_id(previous_stages, "stage-03-routing-owner-gate")
    if not isinstance(stage03, dict):
        return ""
    owners: list[str] = []
    for route in stage03.get("owner_routes") or []:
        if isinstance(route, dict):
            owner = non_empty_string(route.get("owner_id") or route.get("owner"))
            if owner:
                owners.append(owner)
        elif isinstance(route, str) and route.strip():
            owners.append(route.strip())
    for detail in stage03.get("owner_route_details") or []:
        if not isinstance(detail, dict):
            continue
        owner = non_empty_string(detail.get("owner_id") or detail.get("owner"))
        if owner:
            owners.append(owner)
    route_tokens = [split_route_owner_operation(owner)[0] for owner in owners]
    families = ordered_unique(
        [
            family
            for owner in route_tokens
            for family in [canonical_delta_owner(owner)]
            if family and family in DELTA_RESULT_VOCABULARY
        ]
    )
    unmapped = ordered_unique(
        [
            owner
            for owner in owners
            if split_route_owner_operation(owner)[0]
            and not canonical_delta_owner(split_route_owner_operation(owner)[0])
        ]
    )
    if not families and not unmapped:
        return ""
    lines = [
        "",
        "Stage 04 controlled delta_result vocabulary:",
        "- The token after the colon in each `Δ=...:<delta_result>` slot must be one of the source-owned owner-local tokens below.",
        "- The token after the dot in `[owner.operation]` must be one of the source-owned owner-local operation tokens below when a family lists operations.",
        "- Keep route pressure, proof pressure, and result labels out of the operation slot. For example, hidden support belongs in `π=` or `delta_result`, not as `source-status-repair.hidden-support-block`.",
        "- Tokens are family-local proof terms. Do not borrow a token from another owner family; if the chosen owner lacks that token, choose the nearest listed token for the chosen owner or route a different callable owner.",
        "- Some owner operations have operation-specific delta floors. Do not treat a valid family token as proof of a different hidden transition state.",
        "- For M9 predication/identity pressure, use an M9 token such as `predicate-separated`; reserve DO_ATTRIBUTE tokens such as `predicate-identity-separated` for DO_ATTRIBUTE rows.",
        "- Do not invent near-synonyms such as `predicate-transfer-blocked`, `only-scope-defined`, `proof-stack-routed`, or `entailment-bounded`.",
    ]
    if unmapped:
        lines.append(
            "- Routed owners without controlled Stage 04 operation/delta_result vocabulary: "
            + ", ".join(unmapped)
            + ". These routes are not executable ACT owners in this pass; emit HOLD/PARTIAL / "
            "OWNER-BODY-NOT-LOADED / controlled-vocabulary-gap evidence or add source-owned "
            "owner vocabulary with no-model canaries before claiming Land."
        )
    for family in families:
        execution_owner = FAMILY_EXECUTION_OWNER_IDS.get(family)
        if execution_owner:
            lines.append(
                f"- {family} is a delta/register vocabulary family for callable owner "
                f"`{execution_owner}`. Do not use `{family}` as the ACT bracket owner, "
                f"`owner_id`, field_witness owner, or NAR owner_id."
            )
        operations = OWNER_OPERATION_VOCABULARY.get(family)
        if operations:
            lines.append(f"- {family} operations: {', '.join(sorted(operations))}")
        tokens = ", ".join(sorted(DELTA_RESULT_VOCABULARY[family]))
        lines.append(f"- {family}: {tokens}")
        if family == "SOURCE":
            lines.append(
                "- SOURCE is a delta/register vocabulary family, not an executable ACT "
                "owner. Use `authority-order-repair.authority-order-repair` for "
                "`authority-order-repaired`, and `source-status-repair.source-order-repair` "
                "for `source-order-repaired`; keep `SOURCE` only as family/register "
                "classification in non-executable summaries."
            )
            lines.append(
                "- SOURCE formal repair pairing: `authority-order-repaired` requires "
                "`authority-order-repair`; `source-order-repaired` requires "
                "`source-order-repair`. Broad `source-order`/`sort` operations may "
                "use other SOURCE deltas, but they do not prove those compact formal transitions."
            )
            lines.append(
                "- SOURCE formal repair split: authority/rank/tribunal/source-sovereignty "
                "pressure must use `authority-order-repair` with "
                "`authority-order-repaired`; source lineage, quotation chain, "
                "inherited-claim order, source priority, derivation order, or evidential "
                "dependency pressure must use `source-order-repair` with "
                "`source-order-repaired`. Do not convert authority-order pressure into "
                "`source-order-repair` merely because both mention sources."
            )
            lines.append(
                "- SOURCE register-axis floor: authority-order/source-status repairs act "
                "on source/semantic/authority status (`σ`) or explicitly held "
                "source/authority residue (`ξ`). They must not use `Ω` merely because "
                "the burden also names ontological or worship-worthiness pressure; "
                "emit HOLD/PARTIAL if the owner/register target is ambiguous."
            )
            lines.append(
                "- SOURCE pressure-to-delta rule: pressure naming hidden support or "
                "source-order recoil must use `hidden-support-blocked`; proof-text, "
                "proof-stack, or backread hidden-support pressure must use "
                "`proof-text-hidden-support-blocked`. Do not use `authority-order-separated` "
                "or `source-order-repaired` to claim hidden-support blocking."
            )
        if family == "M8":
            lines.append(
                "- M8 operation-specific delta floor: `dependency-trace` requires "
                "`dependency-exposed`. Use `consequence-trace` for consequence or "
                "entailment-blocking work; do not Land `M8.dependency-trace` with "
                "`entailment-blocked`."
            )
        if family == "M9":
            lines.append(
                "- M9 delta_result tokens such as `predicate-separated`, `category-separated`, "
                "`referent-separated`, and `sense-separated` are not callable operations. "
                "Use `M9.predication-repair` or `M9.sense-split` in `[owner.operation]`, "
                "then put the state-change token in the `Δ=...:<delta_result>` slot."
            )
    return "\n".join(lines)


def stage_prompt(
    *,
    root: Path,
    stage_id: str,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
) -> str:
    spec = STAGE_SPECS[stage_id]
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    extra_guidance = ""
    if stage_id == "stage-03-routing-owner-gate":
        extra_guidance = stage03_owner_operation_guidance()
    elif stage_id == "stage-04-burden-execution-act":
        extra_guidance = stage04_delta_vocabulary_guidance(previous_stages)
    custody_metadata = {
        "case_id": case_name,
        "retained_input": rel(raw_input_path, root),
        "input_digest": input_digest,
    }
    custody = json.dumps(custody_metadata, ensure_ascii=False, indent=2)
    return f"""Runtime SHA256: {skill_hash}

You are executing one bounded repo/dev staged current-skill smoke for daee-epistemics.
Use the generated runtime surface at `skill/SKILL.md` as the governing skill source.
The harness supplies the runtime hash, stage contract, raw input, and prior validated stage state;
do not attempt filesystem reads, shell commands, or path access, and do not return `status=fail`
solely because `skill/SKILL.md` is unavailable as a readable file inside the model context.
This is stage only: {stage_id} — {spec['title']}.

Hard boundaries:
- Do not package, tag, upload, publish provenance, or create release assets.
- Do not claim broad model behavior, arbitrary NL-to-IR parsing, guaranteed T_lang uptake, or Graphify/ActiveGraph proof.
- Preserve the public `/daee-epistemics` interface; stage artifacts are repo/dev scratch only.

Run metadata: redacted from model-facing route surface; case IDs and paths are
custody fields only and must not determine routing, owner selection, proof
eligibility, or canonicalization.
Input SHA256: {input_digest}

Custody metadata for Stage 01 only:
```json
{custody}
```

Use the custody metadata only to restate the intake boundary. It is not route
evidence, owner-selection evidence, proof eligibility, canonicalization input,
or a case library key. For Stage 01, copy `case_id`, `input_digest`, and
`retained_input` exactly from this custody block into the JSON response.

Raw input:
```text
{input_text}
```

Previous validated compact stage state:
```json
{previous}
```

Stage task:
{spec['instructions']}
{extra_guidance}

Return exactly one JSON object and nothing else. Required shape:
{{
  "id": "{stage_id}",
  "status": "pass",
  "...": "stage-specific fields"
}}

Required stage-specific fields:
- produces: {spec['produces']}
- requires: {spec['requires']}

If this stage cannot be honestly completed, return the same JSON shape with
`"status": "fail"` and an `"error"` string. Do not invent downstream proof.
"""


def stage07_single_output_mrp_surface_contract(previous_stages: list[dict[str, Any]]) -> str:
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    entries = stage05_per_burden_entries(stage05)
    parts: list[str] = [
        "Per-burden MRP record-surface contract (parity-validated):",
        "- After each line-start superscript landing gate `Land(ⁿB):`, print exactly one `[Mid-Reread Pressure]` block rendered VERBATIM from the matching stage-05 `per_burden_reread` record below.",
        "- Do not invent, merge, or rephrase pressure-activation slots; print all six slot values exactly as recorded.",
        "- Do not summarize the per-burden rereads into one terminal closure block.",
        "- Do not change controlled values: `Finding`, `MRP route result type`, `Route`, `Pre-emption basis`, `Graph delta`.",
        "- If you cannot render a block faithfully from its record, stop and return a held/failed status rather than fabricating block content.",
        "- A record-surface parity validator compares every visible block field to the stage-05 record; any divergence fails Stage 07 release validation.",
    ]
    for entry in entries:
        public = public_burden_id(str(entry.get("burden_id") or ""))
        parts.append("")
        parts.append(f"Block for Land({public}): print exactly:")
        parts.append(staged_output.render_mrp_block(entry))
    return "\n".join(parts)


def release_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
) -> str:
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    field_witness_contract = stage07_field_witness_contract_guidance(previous_stages)
    mrp_surface_contract = stage07_single_output_mrp_surface_contract(previous_stages)
    return f"""Runtime SHA256: {skill_hash}

You are executing stage-07-release-output for one bounded staged current-skill smoke.
Use the generated runtime surface at `skill/SKILL.md` as the governing skill source.
The harness supplies the runtime hash, release contract, raw input, and prior validated stage state;
do not attempt filesystem reads, shell commands, or path access, and do not fail solely because
`skill/SKILL.md` is unavailable as a readable file inside the model context.

Public interface boundary:
- Preserve `/daee-epistemics` governed output shape.
- Preserve the visible opening noetic-field read/header.
- Do not expose raw dev harness internals as a new public mode.

Run metadata: redacted from model-facing route surface; case IDs and paths are
custody fields only and must not determine routing, owner selection, proof
eligibility, or canonicalization.
Input SHA256: {input_digest}

Raw input:
```text
{input_text}
```

Validated compact stage state:
```json
{previous}
```

Produce the final governed `output.md` only.

Required public output surface:
- Preserve the normal visible noetic-field opening/header.
- Include the compact Layer A / Diagnostic IR opening header.
- Include Layer B / ACT rows consistent with the validated Stage 04 state.
- Include MRP/reread/terminal-state surface consistent with Stage 05: one line-start
  superscript `Land(ⁿB):` landing gate per terminal burden, each followed by its
  record-rendered `[Mid-Reread Pressure]` block per the contract below.
- Include parser-stable field_witness/NAR evidence consistent with Stage 06.
- Include visible Closure/Reconstruction Witness diagnostics for `∇·B` and
  `∇×κ`, and include matching machine values in
  `field_witness.coverage_proof.divergence_check` and
  `field_witness.coverage_proof.curl_check`.
- The visible `∇·B` status and coverage `divergence_check` status must be
  identical after status-head normalization.
- The visible `∇×κ` status and coverage `curl_check` status must be
  identical after status-head normalization.
- Include Restorative Response.
- Include Closing Formulation.

{mrp_surface_contract}

Stage07 checker-owned field_witness/NAR clone-state contract:
{field_witness_contract}

Do not include JSON-only stage scratch as the public answer.
Do not include commentary about this harness.
Do not build or claim verifier sidecars, collapse certificates, Grapher output,
B.5 projection sidecars, retained promotion, package operations or provenance
claims, guaranteed uptake, broad model behavior, broad A/B/C/D closure,
Graphify proof, or ActiveGraph proof.
"""


def normalize_release_output_mode(value: str) -> str:
    try:
        return RELEASE_OUTPUT_MODE_ALIASES[value]
    except KeyError as exc:
        allowed = ", ".join(sorted(RELEASE_OUTPUT_MODE_ALIASES))
        raise HarnessError(f"Unknown release output mode {value!r}; expected one of {allowed}") from exc


def validate_compiled_budget_preflight(
    release_output_mode: str,
    target_output_kb: int | None,
    section_expansion_rounds: int,
) -> None:
    target = max(0, int(target_output_kb or 0))
    if release_output_mode != "compiled-output" or target <= 0:
        return
    if section_expansion_rounds > 0:
        return
    raise HarnessError(
        "budgeted compiled output requires --section-expansion-rounds >= 1 "
        "when --target-output-kb > 0 so selected sections can be expanded "
        "before strict assembly validates section budgets"
    )


def compiled_release_section_plan(target_output_kb: int | None) -> list[tuple[str, str]]:
    target = max(0, int(target_output_kb or 0))
    act_chunks = 1 if target <= 0 else max(1, min(8, (target + 24) // 25))
    return [
        ("opening", "visible_opening"),
        ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir"),
        *[(f"act-body-{index}", "layer_b_act") for index in range(1, act_chunks + 1)],
        ("mrp-reread-terminal", "mrp_reread_terminal"),
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
        ("field-witness-nar", "field_witness_nar"),
    ]


SECTION_BUDGET_ROLE_WEIGHTS = {
    "visible_opening": 5,
    "layer_a_diagnostic_ir": 10,
    "layer_b_act": 55,
    "mrp_reread_terminal": 1,
    "field_witness_nar": 1,
    "restorative_response": 18,
    "closing_formulation": 10,
}


def compiled_section_budgets(
    section_plan: list[tuple[str, str]],
    target_output_kb: int | None,
) -> dict[str, Any] | None:
    target_bytes = max(0, int(target_output_kb or 0)) * 1024
    if target_bytes <= 0:
        return None

    role_counts: dict[str, int] = {}
    for _section_id, role in section_plan:
        role_counts[role] = role_counts.get(role, 0) + 1

    role_min_bytes: dict[str, int] = {}
    role_remainders: list[tuple[int, str]] = []
    for role, weight in SECTION_BUDGET_ROLE_WEIGHTS.items():
        numerator = target_bytes * weight
        role_min_bytes[role] = numerator // 100
        role_remainders.append((numerator % 100, role))
    residual = target_bytes - sum(role_min_bytes.values())
    for _remainder, role in sorted(role_remainders, reverse=True)[:residual]:
        role_min_bytes[role] += 1
    min_section_bytes: dict[str, int] = {}
    role_seen: dict[str, int] = {}
    for section_id, role in section_plan:
        role_budget = role_min_bytes.get(role, 0)
        count = max(1, role_counts.get(role, 1))
        seen = role_seen.get(role, 0)
        base = role_budget // count
        remainder = role_budget % count
        min_section_bytes[section_id] = base + (1 if seen < remainder else 0)
        role_seen[role] = seen + 1

    return {
        "schema": staged_output.SECTION_BUDGET_SCHEMA,
        "target_output_bytes": target_bytes,
        "role_min_bytes": role_min_bytes,
        "min_section_bytes": min_section_bytes,
    }


def assemble_compiled_manifest(manifest_path: Path, *, root: Path) -> dict[str, Any]:
    try:
        return staged_output.assemble_manifest(manifest_path, root=root)
    except staged_output.AssemblyError as exc:
        raise HarnessError(f"stage-07-release-output: assembly failed: {exc}") from exc


def partition_body_refs(body_refs: list[str], section_ids: list[str]) -> list[dict[str, Any]]:
    if not section_ids:
        return []
    assignments = [{"section_id": section_id, "body_refs": []} for section_id in section_ids]
    if not body_refs:
        return assignments

    groups: list[list[str]] = []
    for body_ref in body_refs:
        burden_id = body_ref_burden_id(body_ref)
        if groups and burden_id and body_ref_burden_id(groups[-1][-1]) == burden_id:
            groups[-1].append(body_ref)
        else:
            groups.append([body_ref])

    if len(groups) >= len(assignments):
        group_index = 0
        for section_index, assignment in enumerate(assignments):
            remaining_sections = len(assignments) - section_index
            remaining_groups = len(groups) - group_index
            remaining_refs = sum(len(group) for group in groups[group_index:])
            target_refs = max(1, (remaining_refs + remaining_sections - 1) // remaining_sections)
            while group_index < len(groups):
                group = groups[group_index]
                if assignment["body_refs"] and remaining_groups <= remaining_sections:
                    break
                if assignment["body_refs"] and len(assignment["body_refs"]) + len(group) > target_refs:
                    break
                assignment["body_refs"].extend(group)
                group_index += 1
                remaining_groups = len(groups) - group_index
            if section_index == len(assignments) - 1 and group_index < len(groups):
                for group in groups[group_index:]:
                    assignment["body_refs"].extend(group)
                break
        return assignments

    cursor = 0
    total = len(body_refs)
    for section_index, assignment in enumerate(assignments):
        remaining_sections = len(assignments) - section_index
        remaining_refs = total - cursor
        if remaining_refs <= 0:
            break
        take = max(1, (remaining_refs + remaining_sections - 1) // remaining_sections)
        assignment["body_refs"].extend(body_refs[cursor : cursor + take])
        cursor += take
    return assignments


def compiled_act_partition(
    previous_stages: list[dict[str, Any]],
    section_plan: list[tuple[str, str]],
) -> dict[str, Any]:
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    body_refs = list_field(stage04, "act_body_refs")
    act_section_ids = [section_id for section_id, role in section_plan if role == "layer_b_act"]
    if not body_refs:
        raise HarnessError("compiled Stage 07 ACT partition requires Stage 04 act_body_refs")
    return {
        "schema": staged_output.ACT_PARTITION_SCHEMA,
        "assignments": partition_body_refs(body_refs, act_section_ids),
        "no_duplicate_body_refs": True,
        "all_assigned_refs_present": True,
        "contiguous_public_burden_groups": True,
    }


def release_section_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
    section_id: str,
    section_role: str,
    section_number: int,
    section_count: int,
    target_output_kb: int | None,
    section_min_bytes: int = 0,
    assigned_body_refs: list[str] | None = None,
) -> str:
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    target = max(0, int(target_output_kb or 0))
    section_floor = max(0, (target * 1024 + section_count - 1) // section_count) if target else 0
    stage04_for_prompt = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    all_act_body_refs = list_field(stage04_for_prompt, "act_body_refs")
    assigned_for_prompt = assigned_body_refs or []
    first_act_body_ref = all_act_body_refs[0] if all_act_body_refs else ""
    is_first_act_slice = bool(assigned_for_prompt and assigned_for_prompt[0] == first_act_body_ref)
    layer_b_header_instruction = (
        "Include the exact governed header `## Layer B — Bounded Governed Response` because this is the first ACT slice. "
        if is_first_act_slice
        else "Do not emit `## Layer B — Bounded Governed Response`; the first ACT slice owns that single public Layer B header. "
    )
    role_guidance = {
        "visible_opening": (
            "Write only the visible opening for the governed answer. It must contain the exact banner "
            "`daee-epistemics — NOETIC FIELD EXECUTION`, plus the field/read/state surface a "
            "normal `/daee-epistemics` answer exposes. Do not include Layer B, field_witness, "
            "Restorative Response, Closing Formulation, or any `⟦ACT` fence. If the opening needs "
            "to preview live burdens or selected owners, use ordinary prose or bullet text without "
            "ACT-row syntax."
        ),
        "layer_a_diagnostic_ir": (
            "Write only the compact Layer A / Diagnostic IR public surface. It must include a Layer A "
            "Compact DSL/IR or Diagnostic IR header, B_LA, B_MRP, B_total, and Initial burden set "
            "ledger lines. Do not include raw dev harness internals or downstream proof claims."
        ),
        "layer_b_act": (
            "Write only this bounded Layer B / ACT section. "
            + layer_b_header_instruction
            + "ACT-readable rows, body_ref tokens, local operation/result prose, and Land(...) surfaces "
            "consistent with Stage 04. Expand the operation bodies instead of summarizing them. "
            "Do not include MRP, field_witness, Restorative Response, or Closing Formulation. "
            "This section is an ACT partition slice inside one coherent public Layer B body."
        ),
        "mrp_reread_terminal": (
            "Write only the MRP/reread/terminal-state section consistent with Stage 05. It must include "
            "`[Mid-Reread Pressure]`, `R(H,Delta)` or `R(H,Δ)`, terminal states, `MRP route result type`, "
            "`Graph delta`, `Field diagnostics`, and the STOP/HOLD/PARTIAL/RECURSE route consequence. "
            "Do not include final verifier sidecars or retained proof claims."
        ),
        "field_witness_nar": (
            "Write only the Closure/Reconstruction Witness plus parser-stable `field_witness` JSON as the final compiled section after Closing Formulation. "
            "The section must contain a line that begins exactly `field_witness`, then a JSON object "
            "with `B_LA`, `B_MRP`, `B_total`, `coverage_proof`, `owner_activations`, "
            "`normalized_activation_record`, and any generated-burden/formal-reread mirrors required "
            "by Stage 06. The visible divergence/curl statuses must match "
            "`field_witness.coverage_proof.divergence_check` and `.curl_check`. Every visible ACT row "
            "must have exactly one `field_witness.owner_activations[]` mirror with `body_ref`, `owner`, "
            "`owner_id`, `operation`, `pressure`, `delta`, `delta_result`, `land`, `land_target`, "
            "`terminal_state`, `mrp_route_result_type`, and explicit `ordering_role` when those values are visible or validated "
            "upstream. Copy exact ACT-visible owner/operation/pressure/delta/Land values; do not invent "
            "missing proof values and do not add model-authored verification/self-claim fields. Sparse "
            "`owner_activations` are invalid for compiled Stage 07 proof output. Do not use prose-only "
            "`Field Witness` or prose-only `Normalized Activation Record` labels. Do not include Restorative Response or Closing Formulation here."
        ),
        "restorative_response": (
            "Write only the Restorative Response section. Begin with the exact public role heading `Restorative Response`. "
            "Emit that heading exactly once as the first line; do not repeat `Restorative Response` as a later heading or paragraph label. "
            "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint. "
            "It must include these exact parser-stable lines before any extended prose: "
            "`Restored criterion/order: ...`, `Relieved pressure: ...`, and "
            "`Held/scoped/reopenable remainder: ...`. "
            "The remainder line must name any generated or unresolved B_MRP pressure that remains held/scoped/reopenable. "
            "Do not include Closing Formulation here. "
            "Do not claim guaranteed uptake, package operations or provenance claims, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
        "closing_formulation": (
            "Write only the Closing Formulation section. Begin with the exact public role heading `Closing Formulation`. "
            "Emit that heading exactly once as the first line; do not repeat `Closing Formulation` as a later heading or paragraph label. "
            "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint. "
            "It must include explicit high-mass slots for "
            "Established failure, Restored criterion/orientation, and Scoped boundary or Reopen boundary. "
            "Use these exact subsection labels: `### Established failure`, `### Restored criterion/orientation`, and either `### Scoped boundary` or `### Reopen boundary`. "
            "Do not claim guaranteed uptake, package operations or provenance claims, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
    }
    target_line = ""
    if target:
        section_budget_text = (
            f"This section's validator-owned minimum is {section_min_bytes} UTF-8 bytes. "
            if section_min_bytes
            else f"This section's rough share is {section_floor} bytes. "
        )
        target_line = (
            f"\nOverall compiled output floor: at least {target}KB across {section_count} sections. "
            f"{section_budget_text}Expand governed content enough to "
            "help the assembled output meet the floor. The harness will fail the assembly if the "
            "compiled output is under target.\n"
        )
    partition_line = ""
    if section_role == "layer_b_act":
        assigned = assigned_body_refs or []
        assigned_json = json.dumps(assigned, ensure_ascii=False)
        completion_flags_json = json.dumps(body_ref_completion_flags(all_act_body_refs, assigned), ensure_ascii=False)
        partition_line = f"""
ACT partition contract for this section:
- Assigned Stage 04 ACT body_refs: {assigned_json}
- First Stage 04 ACT body_ref for the compiled answer: {json.dumps(first_act_body_ref, ensure_ascii=False)}
- Per-body_ref completion flags for this section: {completion_flags_json}
- Emit ACT rows only for those exact `body_ref=` tokens.
- Do not emit ACT rows for unassigned body_refs, even if they appear in the validated compact stage state.
- Every assigned body_ref must appear exactly once in this section.
- Do not repeat any assigned body_ref in planning prose, examples, or explanatory
  notes; after the one visible ACT row, refer back with prose such as "this submove"
  rather than printing another `body_ref=` token.
- Preserve public burden grouping: body_refs for the same burden must stay contiguous in the final assembled body.
- Emit a burden heading only for a body_ref marked `first_for_burden`; emit a standalone Land/HOLD line only for a body_ref marked `last_for_burden`.
- Do not repeat `## Layer B — Bounded Governed Response` unless this section owns the first Stage 04 ACT body_ref.
- The assembler will fail duplicate, missing, or unassigned ACT body_refs before Stage 07 validators run.
"""
    semantic_contract = ""
    if section_role == "layer_a_diagnostic_ir":
        semantic_contract = stage07_layer_a_contract_guidance(previous_stages)
    elif section_role == "layer_b_act":
        semantic_contract = stage07_act_contract_guidance(previous_stages, assigned_body_refs or [])
    elif section_role == "mrp_reread_terminal":
        semantic_contract = stage07_mrp_reread_contract_guidance(previous_stages)
    elif section_role == "field_witness_nar":
        semantic_contract = stage07_field_witness_contract_guidance(previous_stages)
    return f"""Runtime SHA256: {skill_hash}

You are executing one bounded section of stage-07-release-output for a staged
current-skill smoke. The final public `output.md` will be assembled by repo
tooling from hash-checked section files; do not try to write the whole answer
in this one message.

Public interface boundary:
- Preserve `/daee-epistemics` governed output shape across the assembled file.
- Do not expose raw dev harness internals as a new public mode.
- Do not include commentary about this harness, section manifest, or compiler.
- Do not include private planning, self-talk, scratch analysis, "final answer only"
  reminders, checklist prose, or notes about what you need to write.
- Do not build or claim verifier sidecars, collapse certificates, Grapher output,
  B.5 projection sidecars, retained promotion, package operations or provenance
  claims, guaranteed uptake, broad model behavior, broad A/B/C/D closure,
  Graphify proof, or ActiveGraph proof.
- ACT fence syntax is global across the assembled public output: outside
  `layer_b_act` sections, do not emit any line beginning with `⟦ACT`. Inside
  `layer_b_act`, every visible `⟦ACT ...⟧` row must be copied exactly from the
  canonical Stage 04 row and must include `body_ref=`. Opening summaries, Layer
  A prose, MRP, restoration, closing, and field_witness sections may refer to
  burdens in prose, but they must not invent ACT-looking summary rows.

Run metadata: redacted from model-facing route surface; case IDs and paths are
custody fields only and must not determine routing, owner selection, proof
eligibility, or canonicalization.
Input SHA256: {input_digest}
Section: {section_number} of {section_count}
Section id: {section_id}
Section role: {section_role}
{target_line}
Raw input:
```text
{input_text}
```

Validated compact stage state:
```json
{previous}
```

Section task:
{role_guidance[section_role]}
{partition_line}
{semantic_contract}

Return only the public governed-output text for this section. Do not wrap it in
JSON or code fences. Do not mention that this is a section unless the normal
public governed answer itself needs a section heading.
"""


def release_section_expansion_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_digest: str,
    skill_hash: str,
    section_id: str,
    section_role: str,
    section_min_bytes: int,
    current_bytes: int,
    expansion_round: int,
    max_rounds: int,
    assigned_body_refs: list[str] | None,
    existing_text: str,
) -> str:
    remaining = max(0, section_min_bytes - current_bytes)
    assigned = json.dumps(assigned_body_refs or [], ensure_ascii=False)
    role_notes = {
        "layer_b_act": (
            "Use only the assigned ACT body_refs. Do not add ACT rows for unassigned body_refs. "
            "Do not emit new `⟦ACT` rows or new `body_ref=` tokens during expansion; "
            "expand only owner operation bodies, local result prose, and Land(...) consequences. "
            "Do not repeat the main Layer B bounded heading or print Land(...) before all submoves "
            "for that burden have rendered."
        ),
        "field_witness_nar": (
            "Add human-readable Closure/Reconstruction Witness detail without emitting a second "
            "`field_witness` JSON object and without changing existing JSON proof values."
        ),
        "mrp_reread_terminal": (
            "Expand MRP reread, terminal-state, graph-delta, and field-diagnostic detail without "
            "changing the route result. This section is ledger-only: never print a "
            "`[Mid-Reread Pressure]` heading or block; the harness injects the canonical "
            "per-burden blocks after each `Land(ⁿB):` landing gate from the Stage 05 records."
        ),
        "restorative_response": (
            "Preserve the exact Restorative Response heading and keep the parser-stable lines "
            "`Restored criterion/order:`, `Relieved pressure:`, and "
            "`Held/scoped/reopenable remainder:` visible before any added prose. "
            "Do not repeat the `Restorative Response` heading."
        ),
        "closing_formulation": (
            "Preserve the exact Closing Formulation heading and keep the required public closing slots "
            "visible before any added prose. Do not repeat the `Closing Formulation` heading."
        ),
    }
    return f"""Runtime SHA256: {skill_hash}

You are expanding one already-generated stage-07 compiled output section inside
the same bounded pilot run. This is not a second pilot. The harness will append
your text to the same section file, hash it, and validate the assembled output.

Run metadata: redacted from model-facing route surface; case IDs and paths are
custody fields only and must not determine routing, owner selection, proof
eligibility, or canonicalization.
Input SHA256: {input_digest}
Section id: {section_id}
Section role: {section_role}
Expansion round: {expansion_round} of {max_rounds}
Current section bytes: {current_bytes}
Required section minimum bytes: {section_min_bytes}
Approximate remaining bytes needed: {remaining}
Assigned ACT body_refs for this section: {assigned}

Expansion contract:
- Return only additional public governed-output text for this same section.
- Do not repeat the whole section.
- Do not contradict or replace existing text.
- Do not include JSON or code fences unless the section role itself requires JSON and the added text is valid for that role.
- Do not claim verifier sidecars, retained promotion, package operations or provenance claims, guaranteed uptake, broad model behavior, broad A/B/C/D closure, Graphify proof, or ActiveGraph proof.
- Do not mention this harness, expansion loop, byte budget, manifest, or compiler.
- Do not include private planning, self-talk, scratch analysis, "final answer only"
  reminders, checklist prose, or notes about what you need to write.
- {role_notes.get(section_role, "Add role-local governed detail that stays inside the current section boundary.")}

Existing section text:
```text
{existing_text}
```

Return only the additional text to append.
"""


def write_compiled_release_manifest(
    *,
    root: Path,
    manifest_path: Path,
    case_name: str,
    raw_input_path: Path,
    section_entries: list[dict[str, str]],
    output_path: Path,
    per_burden_reread: list[dict[str, Any]],
    target_output_kb: int = 0,
    act_partition: dict[str, Any] | None = None,
    section_budgets: dict[str, Any] | None = None,
    section_expansions: dict[str, Any] | None = None,
    transport_resume: dict[str, Any] | None = None,
) -> None:
    manifest_dir = manifest_path.parent
    payload: dict[str, Any] = {
        "schema": staged_output.ASSEMBLY_SCHEMA,
        "case_id": case_name,
        "source_input": rel(raw_input_path, root),
        "sections": [
            {
                "id": entry["id"],
                "path": rel(Path(entry["path"]), manifest_dir),
                "sha256": entry["sha256"],
                "role": entry["role"],
            }
            for entry in section_entries
        ],
        "output": {"path": rel(output_path, manifest_dir), "target_output_kb": int(target_output_kb or 0)},
        "per_burden_reread": per_burden_reread,
        "non_claims": {
            "not_release_provenance": True,
            "not_model_behavior_by_itself": True,
            "not_sidecar_proof": True,
        },
    }
    if act_partition is not None:
        payload["act_partition"] = act_partition
    if section_budgets is not None:
        payload["section_budgets"] = section_budgets
    if section_expansions is not None:
        payload["section_expansions"] = section_expansions
    if transport_resume is not None:
        payload["transport_resume"] = transport_resume
    write_json(manifest_path, payload)


def split_text_for_compiled_self_test(text: str) -> list[tuple[str, str, str]]:
    plan = [
        ("opening", "visible_opening"),
        ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir"),
        ("act-body", "layer_b_act"),
        ("mrp-reread-terminal", "mrp_reread_terminal"),
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
        ("field-witness-nar", "field_witness_nar"),
    ]
    layer_b = re.search(r"(?im)^\s*##\s+Layer B\b", text)
    mrp = re.search(r"(?im)^\s*\[Mid-Reread Pressure\]\s*$", text)
    restorative = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Restorative Response\s*$", text)
    closing = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Closing Formulation\s*$", text)
    witness = re.search(r"(?im)^\s*Closure/Reconstruction Witness\s*$", text)
    first_line_end = text.find("\n")
    marker_positions = [
        first_line_end + 1 if first_line_end >= 0 else -1,
        layer_b.start() if layer_b else -1,
        mrp.start() if mrp else -1,
        restorative.start() if restorative else -1,
        closing.start() if closing else -1,
        witness.start() if witness else -1,
    ]
    if all(position >= 0 for position in marker_positions) and marker_positions == sorted(marker_positions):
        layer_a_start, layer_b_start, mrp_start, restorative_start, closing_start, witness_start = marker_positions
        return [
            ("opening", "visible_opening", text[:layer_a_start]),
            ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir", text[layer_a_start:layer_b_start]),
            ("act-body", "layer_b_act", text[layer_b_start:mrp_start]),
            ("mrp-reread-terminal", "mrp_reread_terminal", text[mrp_start:restorative_start]),
            ("restorative-response", "restorative_response", text[restorative_start:closing_start]),
            ("closing-formulation", "closing_formulation", text[closing_start:witness_start]),
            ("field-witness-nar", "field_witness_nar", text[witness_start:]),
        ]

    lines = text.splitlines(keepends=True)
    if len(lines) < len(plan):
        raise HarnessError("Compiled-mode self-test source output is too small to split into required sections")
    chunk_size = max(1, (len(lines) + len(plan) - 1) // len(plan))
    sections: list[tuple[str, str, str]] = []
    cursor = 0
    for index, (section_id, role) in enumerate(plan):
        remaining_sections = len(plan) - index
        remaining_lines = len(lines) - cursor
        take = max(1, remaining_lines - (remaining_sections - 1)) if remaining_sections == 1 else chunk_size
        chunk = "".join(lines[cursor : cursor + take])
        cursor += take
        sections.append((section_id, role, chunk))
    if cursor < len(lines):
        section_id, role, chunk = sections[-1]
        sections[-1] = (section_id, role, chunk + "".join(lines[cursor:]))
    return sections


def run_compiled_release_self_test(
    *,
    root: Path,
    run_dir: Path,
    replay_output_path: Path,
    replay_record: Path,
    replay: dict[str, Any],
    stage07_validation: dict[str, str],
) -> None:
    compiled_dir = run_dir / "compiled-release-self-test"
    source_text = replay_output_path.read_text(encoding="utf-8", errors="replace")
    stage05_replay = stage_by_id(replay["stages"], "stage-05-mrp-reread-terminal-state")
    per_burden_entries = stage05_per_burden_entries(stage05_replay)
    mrp_ledger_section = stage07_mrp_reread_section_scaffold(replay["stages"])
    if not mrp_ledger_section.strip():
        raise HarnessError("Compiled-mode self-test could not derive the ledger-only MRP terminal section")
    section_specs = [
        (section_id, role, mrp_ledger_section if role == "mrp_reread_terminal" else text)
        for section_id, role, text in split_text_for_compiled_self_test(source_text)
    ]
    manifest_path = staged_output.manifest_for_sections(
        compiled_dir,
        case_id="self-test-a9-science-source-stage07-compiled",
        source_input=rel(replay_output_path, root),
        section_specs=section_specs,
        per_burden_reread=per_burden_entries,
    )
    assembly_record = assemble_compiled_manifest(manifest_path, root=root)
    compiled_output_path = root / assembly_record["output"]["path"]
    compiled_validation = run_release_validators(root, compiled_output_path, per_burden_entries)
    compiled_diagnostics = build_release_field_diagnostics(compiled_output_path)
    if compiled_diagnostics.get("matches") is not True:
        raise HarnessError("Compiled-mode self-test output did not produce matching release_field_diagnostics")
    if compiled_validation.get("mrp_record_surface_parity") != "pass":
        raise HarnessError("Compiled-mode self-test did not execute the MRP record-surface parity validator")

    # R1 false-pass canary at the released-output level: tamper one controlled visible
    # value so the block stays shape-valid for check_mid_reread_pressure but no longer
    # mirrors the stage-05 record. Every pre-parity validator must still pass; only the
    # record-surface parity tooth may catch the divergence.
    compiled_text = compiled_output_path.read_text(encoding="utf-8", errors="replace")
    tampered_text = compiled_text.replace("Finding: stable", "Finding: reorientation", 1)
    if tampered_text == compiled_text:
        raise HarnessError("Compiled-mode self-test parity canary could not stage the surface drift")
    tampered_path = compiled_dir / "parity-canary-tampered-output.md"
    write_text(tampered_path, tampered_text)
    require_command_success(
        [sys.executable, str(root / "tools" / "check_mid_reread_pressure.py"), "--outputs", str(tampered_path)],
        cwd=root,
    )
    try:
        run_release_validators(root, tampered_path, per_burden_entries)
    except HarnessError as exc:
        if "record-surface parity" not in str(exc):
            raise
    else:
        raise HarnessError(
            "Compiled-mode self-test accepted a shape-valid visible MRP block that diverges "
            "from the stage-05 per_burden_reread record"
        )

    stage07_local_record = base_record(
        "self-test-a9-science-source-stage07-compiled",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-07-release-output",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage07-compiled",
            replay_record,
            stop_after_stage="stage-07-release-output",
        ),
    )
    stage07_stage = dict(replay["stages"][6])
    stage07_stage["release_output"] = {
        "path": assembly_record["output"]["path"],
        "sha256": assembly_record["output"]["sha256"],
    }
    stage07_stage["release_validation"] = dict(compiled_validation)
    stage07_stage["release_field_diagnostics"] = dict(compiled_diagnostics)
    stage07_stage["release_output_mode"] = "compiled-output"
    stage07_stage["assembly_manifest"] = dict(assembly_record["assembly_manifest"])
    stage07_stage["assembly_hashes"] = dict(assembly_record["hash_record"])
    stage07_local_record["stages"] = [*replay["stages"][:6], stage07_stage]
    compiled_record_path = compiled_dir / "staged-handoff-stage07-compiled-record.json"
    write_json(compiled_record_path, stage07_local_record)
    validate_replay_record(root, compiled_record_path)
    if set(compiled_validation) != set(stage07_validation):
        raise HarnessError("Compiled-mode self-test validator keys drifted from single-output Stage 07 keys")


def build_codex_command(
    root: Path,
    model: str,
    output_path: Path,
    *,
    codex_executable: str | None = None,
) -> list[str]:
    codex = codex_executable or shutil.which("codex")
    if codex is None:
        raise HarnessError("codex CLI not found on PATH; model smoke is blocked by harness/credential environment")
    return [
        codex,
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "-C",
        str(root),
        "-s",
        "read-only",
        "-m",
        model,
        "-c",
        'approval_policy="never"',
        "-c",
        'shell_environment_policy.inherit="all"',
        "--output-last-message",
        str(output_path),
        "-",
    ]


def invoke_codex(root: Path, model: str, prompt: str, output_path: Path, log_path: Path) -> int:
    command = build_codex_command(root, model, output_path)
    result = run_checked(command, cwd=root, input_text=prompt)
    write_text(log_path, result.stdout)
    return result.returncode


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def classify_transport_failure(exit_code: int, log_text: str) -> dict[str, Any]:
    websocket_403_matches = re.findall(
        r"(?is)(?:websocket|wss|ws)[^\n]{0,240}403\s+Forbidden|"
        r"403\s+Forbidden[^\n]{0,240}(?:websocket|wss|ws)",
        log_text,
    )
    http_fallback = re.search(r"(?i)(falling back to HTTP|HTTP fallback|fallback[^\n]{0,120}HTTP)", log_text) is not None
    http_429 = re.search(r"(?i)(429\s+Too Many Requests|Too Many Requests|rate limit)", log_text) is not None
    timeout = TRANSPORT_TIMEOUT_RE.search(log_text) is not None
    semantic_failure = SEMANTIC_FAILURE_RE.search(log_text) is not None
    transport_markers = bool(websocket_403_matches or http_fallback or http_429 or timeout)
    return {
        "websocket_403_count": len(websocket_403_matches),
        "http_fallback": http_fallback,
        "http_429": http_429,
        "timeout_or_network": timeout,
        "semantic_failure_marker": semantic_failure,
        "retryable": exit_code != 0 and transport_markers,
    }


def expansion_subprocess_id(section_id: str, expansion_round: int) -> str:
    safe_section_id = section_id.replace("_", "-")
    return f"stage-07-release-output-{safe_section_id}-expansion-{expansion_round}"


def attempt_path(path: Path, attempt: int) -> Path:
    if attempt <= 1:
        return path
    name = path.name
    for suffix in (".prompt.md", ".codex-log.txt"):
        if name.endswith(suffix):
            return path.with_name(f"{name[:-len(suffix)]}-attempt-{attempt}{suffix}")
    return path.with_name(f"{path.stem}-attempt-{attempt}{path.suffix}")


def path_hash_payload(root: Path, path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"path": rel(path, root), "exists": path.exists()}
    if path.exists() and path.is_file():
        payload["sha256"] = sha256_file(path)
        payload["bytes"] = path.stat().st_size
    return payload


def transport_attempt_record(
    *,
    root: Path,
    subprocess_id: str,
    stage: str,
    role: str,
    section_id: str,
    expansion_round: int,
    attempt: int,
    prompt_path: Path,
    response_path: Path,
    log_path: Path,
    exit_code: int,
    status: str,
    transport: dict[str, Any],
) -> dict[str, Any]:
    return {
        "subprocess_id": subprocess_id,
        "stage": stage,
        "role": role,
        "section_id": section_id,
        "round": expansion_round,
        "attempt": attempt,
        "prompt": path_hash_payload(root, prompt_path),
        "response": path_hash_payload(root, response_path),
        "log": path_hash_payload(root, log_path),
        "exit_code": exit_code,
        "status": status,
        "transport": transport,
    }


def write_transport_attempts_record(path: Path, *, root: Path, attempts: list[dict[str, Any]]) -> None:
    write_json(
        path,
        {
            "schema": TRANSPORT_ATTEMPTS_SCHEMA,
            "attempt_count": len(attempts),
            "attempts": attempts,
        },
    )


def resolve_hash_payload_path(root: Path, payload: dict[str, Any], key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, dict) or not isinstance(value.get("path"), str):
        raise HarnessError(f"Resume hash record missing {key}.path")
    return resolve_under_root(root, Path(value["path"]), f"Resume {key}")


def validate_hash_payload_file(root: Path, item: dict[str, Any], label: str) -> Path:
    if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
        raise HarnessError(f"{label}: missing path or sha256")
    path = resolve_under_root(root, Path(item["path"]), label)
    if not path.exists() or not path.is_file():
        raise HarnessError(f"{label}: hashed artifact is missing: {rel(path, root)}")
    actual = sha256_file(path)
    expected = item["sha256"].upper()
    if actual != expected:
        raise HarnessError(f"{label}: hash mismatch for {rel(path, root)}; expected {expected} but found {actual}")
    return path


def hash_artifact_map(root: Path, hash_payload: dict[str, Any]) -> tuple[dict[str, str], list[Path]]:
    artifacts = hash_payload.get("stage_artifacts")
    if not isinstance(artifacts, list):
        raise HarnessError("Resume hash record stage_artifacts must be a list")
    artifact_hashes: dict[str, str] = {}
    artifact_paths: list[Path] = []
    for index, item in enumerate(artifacts):
        path = validate_hash_payload_file(root, item, f"stage_artifacts[{index}]")
        artifact_hashes[rel(path, root)] = item["sha256"].upper()
        artifact_paths.append(path)
    for key in ("skill", "replay_record", "raw_input"):
        validate_hash_payload_file(root, hash_payload.get(key, {}), key)
    return artifact_hashes, artifact_paths


def require_hash_matched(path: Path, *, root: Path, artifact_hashes: dict[str, str], label: str) -> None:
    key = rel(path, root)
    expected = artifact_hashes.get(key)
    if expected is None:
        raise HarnessError(f"{label}: missing from prior hash record: {key}")
    if not path.exists() or not path.is_file():
        raise HarnessError(f"{label}: missing prior artifact: {key}")
    actual = sha256_file(path)
    if actual != expected:
        raise HarnessError(f"{label}: hash mismatch for {key}; expected {expected} but found {actual}")


def parse_stage07_expansion_failure(message: str) -> dict[str, Any]:
    match = re.search(
        r"stage-07-release-output\s+([A-Za-z0-9_-]+)\s+expansion\s+([0-9]+):"
        r".*?see\s+([^\r\n]+?\.codex-log\.txt)",
        message,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        raise HarnessError("Resume failure record does not identify a Stage 07 expansion subprocess")
    return {
        "section_id": match.group(1),
        "round": int(match.group(2)),
        "log_path": Path(match.group(3).strip()),
    }


def load_stage07_resume_context(root: Path, run_dir: Path) -> dict[str, Any]:
    hash_path = run_dir / "staged-smoke.hashes.json"
    failure_record_path = run_dir / "records" / "staged-handoff-failure.json"
    if not hash_path.exists():
        raise HarnessError(f"Resume run missing hash record: {rel(hash_path, root)}")
    if not failure_record_path.exists():
        raise HarnessError(f"Resume run missing failure record: {rel(failure_record_path, root)}")
    for forbidden in (
        run_dir / "output.md",
        run_dir / "stage-07-output-assembly.manifest.json",
        run_dir / "output.md.assembly.hashes.json",
    ):
        if forbidden.exists():
            raise HarnessError(f"Resume refuses run with existing final/assembly artifact: {rel(forbidden, root)}")
    for forbidden_dir in (run_dir / "proof-sidecars", run_dir / "retained-promotion"):
        if forbidden_dir.exists() and any(forbidden_dir.iterdir()):
            raise HarnessError(f"Resume refuses run with downstream sidecars/promotion: {rel(forbidden_dir, root)}")

    hash_payload = load_json(hash_path)
    failure_payload = load_json(failure_record_path)
    if not isinstance(hash_payload, dict) or not isinstance(failure_payload, dict):
        raise HarnessError("Resume records must be JSON objects")
    artifact_hashes, artifact_paths = hash_artifact_map(root, hash_payload)
    stages = failure_payload.get("stages")
    if not isinstance(stages, list) or len(stages) != 6:
        raise HarnessError("Resume requires exactly completed Stage 01-06 records")
    expected_stage_ids = STAGE_ORDER[:6]
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict) or stage.get("id") != expected_stage_ids[index] or stage.get("status") != "pass":
            raise HarnessError("Resume requires Stage 01-06 to be present and pass")
    failure = failure_payload.get("failure")
    if not isinstance(failure, str) or not failure.strip():
        raise HarnessError("Resume failure record must include a failure string")
    failed = parse_stage07_expansion_failure(failure)
    log_path = resolve_under_root(root, failed["log_path"], "failed expansion log")
    require_hash_matched(log_path, root=root, artifact_hashes=artifact_hashes, label="failed expansion log")
    transport = classify_transport_failure(1, read_text_if_exists(log_path))
    if transport.get("retryable") is not True:
        raise HarnessError("Resume failure is not classified as retryable transport")

    log_name_match = re.search(
        r"stage-07-release-output-([0-9]+)-(.+)-expansion-([0-9]+)\.codex-log\.txt$",
        log_path.name,
    )
    if log_name_match is None:
        raise HarnessError("Resume failed expansion log name is not parseable")
    section_index = int(log_name_match.group(1))
    safe_section_id = log_name_match.group(2)
    expansion_round = int(log_name_match.group(3))
    prompt_path = run_dir / "prompts" / f"stage-07-release-output-{section_index:02d}-{safe_section_id}-expansion-{expansion_round}.prompt.md"
    response_path = run_dir / "release-section-expansions" / f"{section_index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
    require_hash_matched(prompt_path, root=root, artifact_hashes=artifact_hashes, label="failed expansion prompt")
    prior_attempt = transport_attempt_record(
        root=root,
        subprocess_id=expansion_subprocess_id(failed["section_id"], failed["round"]),
        stage="stage-07-release-output",
        role=failed["section_id"].replace("-", "_"),
        section_id=failed["section_id"],
        expansion_round=failed["round"],
        attempt=1,
        prompt_path=prompt_path,
        response_path=response_path,
        log_path=log_path,
        exit_code=1,
        status="failed_transport",
        transport=transport,
    )
    return {
        "schema": TRANSPORT_RESUME_SCHEMA,
        "run_dir": rel(run_dir, root),
        "hash_record": rel(hash_path, root),
        "failure_record": rel(failure_record_path, root),
        "raw_input_path": resolve_hash_payload_path(root, hash_payload, "raw_input"),
        "replay_record_path": resolve_hash_payload_path(root, hash_payload, "replay_record"),
        "stages": [dict(stage) for stage in stages],
        "artifact_hashes": artifact_hashes,
        "artifact_paths": artifact_paths,
        "failed_expansion": {
            "section_id": failed["section_id"],
            "section_index": section_index,
            "safe_section_id": safe_section_id,
            "round": failed["round"],
            "log_path": rel(log_path, root),
        },
        "prior_attempts": [prior_attempt],
    }


def existing_expansion_records_for_resume(
    *,
    root: Path,
    run_dir: Path,
    section_plan: list[tuple[str, str]],
    max_rounds: int,
    artifact_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    expansions_dir = run_dir / "release-section-expansions"
    for index, (section_id, section_role) in enumerate(section_plan, start=1):
        safe_section_id = section_id.replace("_", "-")
        for expansion_round in range(1, max_rounds + 1):
            expansion_path = expansions_dir / f"{index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
            if not expansion_path.exists():
                continue
            require_hash_matched(
                expansion_path,
                root=root,
                artifact_hashes=artifact_hashes,
                label="prior successful expansion",
            )
            records.append(
                {
                    "section_id": section_id,
                    "role": section_role,
                    "round": expansion_round,
                    "path": str(expansion_path),
                    "sha256": sha256_file(expansion_path),
                }
            )
    return records


def invoke_expansion_with_transport_policy(
    *,
    root: Path,
    model: str,
    prompt: str,
    base_prompt_path: Path,
    base_output_path: Path,
    base_log_path: Path,
    section_id: str,
    section_role: str,
    expansion_round: int,
    first_attempt: int,
    retry_rounds: int,
    attempts: list[dict[str, Any]],
    attempts_record_path: Path,
    stage_files: list[Path],
) -> Path:
    if retry_rounds < 0:
        raise HarnessError("--transport-retry-rounds must be a non-negative integer")
    subprocess_id = expansion_subprocess_id(section_id, expansion_round)
    last_attempt = first_attempt + retry_rounds
    for attempt in range(first_attempt, last_attempt + 1):
        prompt_path = attempt_path(base_prompt_path, attempt)
        output_path = attempt_path(base_output_path, attempt)
        log_path = attempt_path(base_log_path, attempt)
        write_text(prompt_path, prompt)
        exit_code = invoke_codex(root, model, prompt, output_path, log_path)
        stage_files.extend([prompt_path, output_path, log_path])
        log_text = read_text_if_exists(log_path)
        transport = classify_transport_failure(exit_code, log_text)
        if exit_code == 0:
            if not output_path.exists() or output_path.stat().st_size == 0:
                attempts.append(
                    transport_attempt_record(
                        root=root,
                        subprocess_id=subprocess_id,
                        stage="stage-07-release-output",
                        role=section_role,
                        section_id=section_id,
                        expansion_round=expansion_round,
                        attempt=attempt,
                        prompt_path=prompt_path,
                        response_path=output_path,
                        log_path=log_path,
                        exit_code=exit_code,
                        status="failed_semantic",
                        transport=transport,
                    )
                )
                write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
                raise HarnessError(
                    f"stage-07-release-output {section_id} expansion {expansion_round}: "
                    "expansion output was not produced"
                )
            attempts.append(
                transport_attempt_record(
                    root=root,
                    subprocess_id=subprocess_id,
                    stage="stage-07-release-output",
                    role=section_role,
                    section_id=section_id,
                    expansion_round=expansion_round,
                    attempt=attempt,
                    prompt_path=prompt_path,
                    response_path=output_path,
                    log_path=log_path,
                    exit_code=exit_code,
                    status="pass",
                    transport=transport,
                )
            )
            write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
            return output_path
        status = "failed_transport" if transport.get("retryable") is True else "failed_non_transport"
        attempts.append(
            transport_attempt_record(
                root=root,
                subprocess_id=subprocess_id,
                stage="stage-07-release-output",
                role=section_role,
                section_id=section_id,
                expansion_round=expansion_round,
                attempt=attempt,
                prompt_path=prompt_path,
                response_path=output_path,
                log_path=log_path,
                exit_code=exit_code,
                status=status,
                transport=transport,
            )
        )
        write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
        if transport.get("retryable") is not True:
            raise HarnessError(
                f"stage-07-release-output {section_id} expansion {expansion_round}: "
                f"codex exec failed with exit code {exit_code}; see {rel(log_path, root)}"
            )
        if attempt == last_attempt:
            raise HarnessError(
                f"stage-07-release-output {section_id} expansion {expansion_round}: "
                f"transport retry budget exhausted after {attempt - first_attempt + 1} attempt(s); "
                f"see {rel(log_path, root)}"
            )
    raise HarnessError("transport retry loop exited unexpectedly")


def stage_order_for_stop(stop_after_stage: str | None) -> list[str]:
    if stop_after_stage is None:
        return list(STAGE_ORDER)
    if stop_after_stage not in STAGE_ORDER:
        raise HarnessError(f"Unknown stop-after-stage value: {stop_after_stage}")
    return STAGE_ORDER[: STAGE_ORDER.index(stop_after_stage) + 1]


def handoffs_for_stage_order(stage_order: list[str]) -> list[dict[str, Any]]:
    included = set(stage_order)
    return [dict(handoff) for handoff in HANDOFFS if handoff["from"] in included and handoff["to"] in included]


def model_scope(case_name: str, replay_record: Path, *, stop_after_stage: str | None) -> dict[str, Any]:
    del case_name
    return {
        "type": "focused-current-skill-stage-smoke" if stop_after_stage else "focused-current-skill-smoke",
        "case_count": 1,
        "case_family": "metadata-redacted-dsl-ir-selected-by-input",
        "case_metadata_role": "custody_only_not_route_or_proof",
        "retained_replay_target": rel(replay_record),
    }


def base_record(
    case_name: str,
    mode: str,
    *,
    not_model_smoke: bool,
    stop_after_stage: str | None = None,
    model_scope_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage_order = stage_order_for_stop(stop_after_stage)
    non_claims = dict(NO_MODEL_NON_CLAIMS if not_model_smoke else MODEL_NON_CLAIMS)
    non_claims["not_model_smoke"] = not_model_smoke
    record: dict[str, Any] = {
        "schema": "staged-runtime-handshake-v1",
        "case_id": case_name,
        "mode": mode,
        "user_interface_preserved": True,
        "stage_order": stage_order,
        "stages": [],
        "handoffs": handoffs_for_stage_order(stage_order),
        "non_claims": non_claims,
    }
    if stop_after_stage is not None:
        stop_index = STAGE_ORDER.index(stop_after_stage)
        release_index = STAGE_ORDER.index("stage-07-release-output")
        verifier_index = STAGE_ORDER.index("stage-08-verifier-sidecars")
        record["stage_scope"] = {
            "stop_after_stage": stop_after_stage,
            "stage_count": len(stage_order),
            "not_verifier_sidecars": stop_index < verifier_index,
        }
        if stop_index < release_index:
            record["stage_scope"]["not_release_output"] = True
        else:
            record["stage_scope"]["release_output"] = True
    if model_scope_payload is not None:
        record["model_scope"] = model_scope_payload
    return record


def write_hash_record(
    path: Path,
    *,
    root: Path,
    case_name: str,
    mode: str,
    model: str | None,
    skill_path: Path,
    replay_record: Path,
    raw_input_path: Path,
    run_dir: Path,
    stage_files: list[Path],
    handoff_record: Path | None,
    output_path: Path | None,
    sidecar_paths: list[Path],
    verdict: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "staged-current-skill-smoke-hashes-v1",
        "case_name": case_name,
        "mode": mode,
        "model": model,
        "verdict": verdict,
        "run_dir": rel(run_dir, root),
        "skill": {"path": rel(skill_path, root), "sha256": sha256_file(skill_path)},
        "replay_record": {"path": rel(replay_record, root), "sha256": sha256_file(replay_record)},
        "raw_input": {"path": rel(raw_input_path, root), "sha256": sha256_file(raw_input_path)},
        "stage_artifacts": [
            {"path": rel(path_item, root), "sha256": sha256_file(path_item)}
            for path_item in stage_files
            if path_item.exists()
        ],
        "handoff_record": None,
        "output": None,
        "sidecars": [
            {"path": rel(path_item, root), "sha256": sha256_file(path_item)}
            for path_item in sidecar_paths
            if path_item.exists()
        ],
        "non_claims": {
            "not_package_provenance": True,
            "not_retained_promotion": True,
            "not_broad_model_matrix": True,
            "not_graphify_or_activegraph_proof": True,
        },
    }
    if handoff_record is not None and handoff_record.exists():
        payload["handoff_record"] = {"path": rel(handoff_record, root), "sha256": sha256_file(handoff_record)}
    if output_path is not None and output_path.exists():
        payload["output"] = {"path": rel(output_path, root), "sha256": sha256_file(output_path)}
    write_json(path, payload)
    return payload


def run_self_test(root: Path) -> int:
    global invoke_codex
    files = validate_required_files(root)
    replay_record = DEFAULT_REPLAY_RECORD
    raw_input = DEFAULT_INPUT
    validate_replay_record(root, replay_record)
    smoke_command = build_codex_command(
        root,
        "gpt-5.5",
        root / ".daee" / "validation" / "self-test-output.txt",
        codex_executable="codex",
    )
    if "--ignore-user-config" not in smoke_command or "--ephemeral" not in smoke_command:
        raise HarnessError("Self-test Codex subprocess command did not isolate mutable user config")
    if 'approval_policy="never"' not in smoke_command or 'shell_environment_policy.inherit="all"' not in smoke_command:
        raise HarnessError("Self-test Codex subprocess command lost approval/environment policy")
    replay = load_json(replay_record)
    named_scope = model_scope("self-test-a9-science-source", replay_record, stop_after_stage=None)
    neutral_scope = model_scope("neutral-formal-route-copy", replay_record, stop_after_stage=None)
    if named_scope != neutral_scope:
        raise HarnessError("Self-test model_scope changed under neutral case-name copy")
    if named_scope.get("case_family") == "self-test-a9-science-source" or "a9-science-source" in str(
        named_scope.get("case_family") or ""
    ):
        raise HarnessError("Self-test model_scope derived proof-facing case_family from case name")
    if named_scope.get("case_metadata_role") != "custody_only_not_route_or_proof":
        raise HarnessError("Self-test model_scope did not mark case metadata as custody-only")
    malformed_stage_responses = (
        '{"id":"stage-02-layer-a-diagnostic-ir","status":"pass"}}',
        '{"id":"stage-02-layer-a-diagnostic-ir","status":"pass"}{"id":"extra","status":"pass"}',
    )
    for malformed_response in malformed_stage_responses:
        try:
            extract_json_object(malformed_response)
        except HarnessError as exc:
            if "json_parse_failure" not in str(exc):
                raise HarnessError("Self-test malformed Stage JSON did not classify as json_parse_failure") from exc
        else:
            raise HarnessError("Self-test accepted malformed multi-object Stage JSON as canonical proof")
    prompt_a = stage_prompt(
        root=root,
        stage_id=STAGE_ORDER[0],
        case_name="self-test-a9-science-source",
        raw_input_path=DEFAULT_INPUT,
        input_text="/daee-epistemics refute secularism",
        input_digest="0" * 64,
        skill_hash="1" * 64,
        previous_stages=[],
    )
    prompt_b = stage_prompt(
        root=root,
        stage_id=STAGE_ORDER[0],
        case_name="neutral-formal-route-copy",
        raw_input_path=DEFAULT_INPUT.parent / "neutral-copy.md",
        input_text="/daee-epistemics refute secularism",
        input_digest="0" * 64,
        skill_hash="1" * 64,
        previous_stages=[],
    )

    def redact_stage01_custody(prompt: str) -> str:
        return re.sub(
            r"(?s)Custody metadata for Stage 01 only:\n```json\n.*?\n```\n\n",
            "Custody metadata for Stage 01 only:\n```json\n<CUSTODY_ONLY_REDACTED>\n```\n\n",
            prompt,
            count=1,
        )

    if redact_stage01_custody(prompt_a) != redact_stage01_custody(prompt_b):
        raise HarnessError("Self-test stage prompt changed outside the Stage 01 custody block")
    for prompt, case_id, retained_path in (
        (prompt_a, "self-test-a9-science-source", rel(DEFAULT_INPUT, root)),
        (prompt_b, "neutral-formal-route-copy", rel(DEFAULT_INPUT.parent / "neutral-copy.md", root)),
    ):
        custody_start = prompt.find("Custody metadata for Stage 01 only:")
        raw_start = prompt.find("Raw input:")
        if custody_start < 0 or raw_start < custody_start:
            raise HarnessError("Self-test Stage 01 prompt missing bounded custody block")
        custody_slice = prompt[custody_start:raw_start]
        non_custody = prompt[:custody_start] + prompt[raw_start:]
        for expected in (f'"case_id": "{case_id}"', f'"retained_input": "{retained_path}"'):
            if expected not in custody_slice:
                raise HarnessError(f"Self-test Stage 01 custody block missing {expected!r}")
            if expected in non_custody:
                raise HarnessError(f"Self-test Stage 01 custody value leaked outside custody block: {expected!r}")
    for invariant in (
        "custody fields only and must not determine routing, owner selection, proof",
        "Use the custody metadata only to restate the intake boundary",
        "For Stage 01, copy `case_id`, `input_digest`, and",
    ):
        if invariant not in prompt_a:
            raise HarnessError(f"Self-test Stage 01 custody prompt missing invariant {invariant!r}")
    stage02_prompt = stage_prompt(
        root=root,
        stage_id="stage-02-layer-a-diagnostic-ir",
        case_name="self-test-a9-science-source",
        raw_input_path=DEFAULT_INPUT,
        input_text="/daee-epistemics refute secularism",
        input_digest="0" * 64,
        skill_hash="1" * 64,
        previous_stages=[
            {
                "id": "stage-01-intake",
                "status": "pass",
                "input_digest": "0" * 64,
            }
        ],
    )
    for invariant in (
        "do not attempt filesystem reads",
        "do not return `status=fail`",
        "`skill/SKILL.md` is unavailable as a readable path",
        "`skill/SKILL.md` is unavailable as a readable file",
    ):
        if invariant not in stage02_prompt:
            raise HarnessError(f"Self-test Stage 02 prompt missing no-filesystem-read invariant {invariant!r}")
    run_dir = root / ".daee" / "validation" / f"staged-current-skill-harness-self-test-{uuid.uuid4().hex}"
    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    literal_input_dir = run_dir / "raw-input-literal"
    literal_input_path = materialize_smoke_raw_input(
        root,
        literal_input_dir,
        DEFAULT_INPUT,
        "/daee-epistemics refute secularism",
    )
    if literal_input_path.read_text(encoding="utf-8") != "/daee-epistemics refute secularism\n":
        raise HarnessError("Self-test raw literal input was not materialized exactly")
    try:
        materialize_smoke_raw_input(
            root,
            literal_input_dir,
            DEFAULT_INPUT.parent / "alternate-input.md",
            "/daee-epistemics refute secularism",
        )
    except HarnessError as exc:
        if "mutually exclusive" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test raw literal input accepted a simultaneous raw-input-path")
    path_preflight_input = run_dir / "slash-command-input.md"
    write_text(path_preflight_input, "/neutral-command refute a compound prompt\n")
    preflight_smoke_inputs(
        argparse.Namespace(
            case_name="neutral-slash-input-preflight",
            raw_input=None,
            raw_input_path=path_preflight_input,
            replay_record=replay_record,
            run_dir=run_dir / "path-input-preflight-run",
            resume_run_dir=None,
        ),
        root,
        emit=False,
    )
    preflight_smoke_inputs(
        argparse.Namespace(
            case_name="neutral-literal-input-preflight",
            raw_input="/neutral-command refute a compound prompt",
            raw_input_path=DEFAULT_INPUT,
            replay_record=replay_record,
            run_dir=run_dir / "literal-input-preflight-run",
            resume_run_dir=None,
        ),
        root,
        emit=False,
    )
    try:
        preflight_smoke_inputs(
            argparse.Namespace(
                case_name="invalid-mixed-input-preflight",
                raw_input="/neutral-command refute a compound prompt",
                raw_input_path=path_preflight_input,
                replay_record=replay_record,
                run_dir=run_dir / "invalid-mixed-input-preflight-run",
                resume_run_dir=None,
            ),
            root,
            emit=False,
        )
    except HarnessError as exc:
        if "mutually exclusive" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test input preflight accepted simultaneous literal and path inputs")
    existing_preflight_run = run_dir / "existing-input-preflight-run"
    existing_preflight_run.mkdir(parents=True)
    try:
        preflight_smoke_inputs(
            argparse.Namespace(
                case_name="invalid-existing-run-preflight",
                raw_input=None,
                raw_input_path=path_preflight_input,
                replay_record=replay_record,
                run_dir=existing_preflight_run,
                resume_run_dir=None,
            ),
            root,
            emit=False,
        )
    except HarnessError as exc:
        if "Run directory already exists" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test input preflight accepted an existing run directory")
    stage_files: list[Path] = []
    for stage in replay["stages"]:
        stage_path = stages_dir / f"{stage['id']}.response.json"
        write_json(stage_path, stage)
        stage_files.append(stage_path)
    record_path = run_dir / "staged-handoff-record.json"
    write_json(record_path, replay)
    validate_replay_record(root, record_path)
    hash_path = run_dir / "staged-smoke.hashes.json"
    write_hash_record(
        hash_path,
        root=root,
        case_name="self-test-a9-science-source",
        mode="self-test-no-model",
        model=None,
        skill_path=files["skill"],
        replay_record=replay_record,
        raw_input_path=raw_input,
        run_dir=run_dir,
        stage_files=stage_files,
        handoff_record=record_path,
        output_path=None,
        sidecar_paths=[],
        verdict="SELF_TEST_NO_MODEL_PASS",
    )
    loaded_hashes = load_json(hash_path)
    if loaded_hashes.get("mode") != "self-test-no-model":
        raise HarnessError("Self-test hash record did not preserve self-test mode")
    if loaded_hashes.get("model") is not None:
        raise HarnessError("Self-test hash record must not claim a model invocation")
    transport_log = (
        "websocket attempt failed: 403 Forbidden\n"
        "falling back to HTTP transport\n"
        "HTTP status: 429 Too Many Requests\n"
    )
    transport_classification = classify_transport_failure(1, transport_log)
    if transport_classification.get("retryable") is not True:
        raise HarnessError("Self-test failed to classify websocket 403/HTTP 429 as retryable transport")
    if transport_classification.get("websocket_403_count") != 1 or transport_classification.get("http_429") is not True:
        raise HarnessError("Self-test transport classification missed 403 or 429 markers")
    semantic_classification = classify_transport_failure(
        1,
        "AssemblyError: validation failed; missing required surface in public output",
    )
    if semantic_classification.get("retryable") is True:
        raise HarnessError("Self-test classified semantic validator failure as retryable transport")
    if attempt_path(Path("response.md"), 2).name != "response-attempt-2.md":
        raise HarnessError("Self-test attempt path did not suffix markdown response")
    if attempt_path(Path("call.codex-log.txt"), 2).name != "call-attempt-2.codex-log.txt":
        raise HarnessError("Self-test attempt path did not suffix codex log")
    eligible_certificate = {
        "collapse_positive": True,
        "coverage_complete": True,
        "diagnostic_completeness": True,
        "hold_partial_nodes": [],
    }
    if b5_projection_eligibility_errors(eligible_certificate):
        raise HarnessError("Self-test rejected a B.5 projection-eligible certificate")
    ineligible_certificate = {
        "collapse_positive": False,
        "coverage_complete": False,
        "diagnostic_completeness": True,
        "hold_partial_nodes": [{"id": "B6", "state": "carried-RECURSE"}],
    }
    eligibility_errors = b5_projection_eligibility_errors(ineligible_certificate)
    for expected in (
        "collapse_positive must be true before B.5 projection",
        "coverage_complete must be true before B.5 projection",
        "hold_partial_nodes must be empty before B.5 projection",
    ):
        if expected not in eligibility_errors:
            raise HarnessError(f"Self-test B.5 projection eligibility missed {expected!r}")
    eligibility_record = run_dir / "b5-full-ir-projection-eligibility.json"
    write_b5_projection_ineligibility(
        root=root,
        certificate_path=run_dir / "collapse-certificate.json",
        eligibility_path=eligibility_record,
        errors=eligibility_errors,
    )
    loaded_eligibility = load_json(eligibility_record)
    if loaded_eligibility.get("eligible") is not False:
        raise HarnessError("Self-test B.5 ineligibility record did not preserve eligible=false")
    non_claims = loaded_eligibility.get("non_claims")
    if not isinstance(non_claims, dict) or non_claims.get("not_b5_projection_sidecar") is not True:
        raise HarnessError("Self-test B.5 ineligibility record did not preserve non-claim boundary")
    source_stack_like_stages = [
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "selected_n_frame": "source-stack-status-self-test",
            "burden_floor": ["B1", "B2", "B3"],
            "burden_registers": {
                "B1": ["source-status", "transmission"],
                "B2": ["proof-stack"],
                "B3": ["consequence"],
            },
        },
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "B_LA": ["B1", "B2", "B3"],
            "generated_burdens": [
                {"id": "B4", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary"}
            ],
            "unresolved_burdens": ["B4"],
            "terminal_states": {
                "B1": "landed",
                "B2": "carried-RECURSE",
                "B3": "carried-RECURSE",
                "B4": "carried-RECURSE",
            },
        },
        {
            "id": "stage-06-field-witness-nar",
            "B_LA": ["B1", "B2", "B3"],
            "B_MRP": ["B4"],
            "unresolved_burdens": ["B4"],
            "selected_n_frame": "source-stack-status-self-test",
        },
    ]
    source_stack_supplement = (
        stage07_restorative_response_section_scaffold(source_stack_like_stages)
        + "\n"
        + stage07_closing_formulation_budget_supplement(source_stack_like_stages)
    )
    for forbidden in (
        "Father",
        "Messiah",
        "John",
        "Trinitarian",
        "verse's predicate",
        "co-knowledge",
        "sender-sent",
        "worship-orientation",
    ):
        if forbidden.lower() in source_stack_supplement.lower():
            raise HarnessError(f"Self-test source-stack closing scaffold leaked case-specific term {forbidden!r}")

    def artifact(path: Path) -> dict[str, str]:
        return {"path": rel(path, root), "sha256": sha256_file(path)}

    def write_resume_fixture(name: str) -> Path:
        fixture_dir = run_dir / name
        fixture_prompts = fixture_dir / "prompts"
        fixture_responses = fixture_dir / "responses"
        fixture_sections = fixture_dir / "release-sections"
        fixture_records = fixture_dir / "records"
        for directory in (fixture_prompts, fixture_responses, fixture_sections, fixture_records):
            directory.mkdir(parents=True, exist_ok=True)
        fixture_raw_input = fixture_dir / "raw-input.md"
        failed_prompt = fixture_prompts / "stage-07-release-output-08-restorative-response-expansion-1.prompt.md"
        failed_log = fixture_responses / "stage-07-release-output-08-restorative-response-expansion-1.codex-log.txt"
        section_output = fixture_sections / "08-restorative-response.md"
        write_text(fixture_raw_input, "Selected worldview test fixture input.\n")
        write_text(failed_prompt, "Expand restorative response.\n")
        write_text(failed_log, transport_log)
        write_text(section_output, "## Restorative Response\n\nBase section text.\n")
        failure_record = fixture_records / "staged-handoff-failure.json"
        write_json(
            failure_record,
            {
                "schema": "staged-runtime-handshake-v1",
                "case_id": "self-test-transport-resume",
                "mode": "staged-current-skill-smoke",
                "stage_order": STAGE_ORDER,
                "stages": [dict(stage) for stage in replay["stages"][:6]],
                "handoffs": handoffs_for_stage_order(STAGE_ORDER),
                "non_claims": MODEL_NON_CLAIMS,
                "failure": (
                    "stage-07-release-output restorative-response expansion 1: "
                    f"codex exec failed with exit code 1; see {rel(failed_log, root)}"
                ),
            },
        )
        write_json(
            fixture_dir / "staged-smoke.hashes.json",
            {
                "schema": "staged-current-skill-smoke-hashes-v1",
                "case_name": "self-test-transport-resume",
                "mode": "staged-current-skill-smoke",
                "model": "fake-model",
                "verdict": "STAGED_MODEL_HARNESS_NEGATIVE_EVIDENCE: transport fixture",
                "run_dir": rel(fixture_dir, root),
                "skill": artifact(files["skill"]),
                "replay_record": artifact(replay_record),
                "raw_input": artifact(fixture_raw_input),
                "stage_artifacts": [
                    artifact(failed_prompt),
                    artifact(section_output),
                    artifact(failed_log),
                    artifact(failure_record),
                ],
                "handoff_record": artifact(failure_record),
                "output": None,
                "sidecars": [],
                "non_claims": {
                    "not_package_provenance": True,
                    "not_retained_promotion": True,
                    "not_broad_model_matrix": True,
                    "not_graphify_or_activegraph_proof": True,
                },
            },
        )
        return fixture_dir

    resume_fixture = write_resume_fixture("transport-resume-valid")
    resume_context = load_stage07_resume_context(root, resume_fixture)
    if resume_context["failed_expansion"].get("section_id") != "restorative-response":
        raise HarnessError("Self-test resume preflight did not identify the failed expansion section")
    if resume_context["prior_attempts"][0].get("status") != "failed_transport":
        raise HarnessError("Self-test resume preflight did not record the failed transport attempt")

    hash_mismatch_fixture = write_resume_fixture("transport-resume-hash-mismatch")
    write_text(hash_mismatch_fixture / "release-sections" / "08-restorative-response.md", "mutated\n")
    try:
        load_stage07_resume_context(root, hash_mismatch_fixture)
    except HarnessError as exc:
        if "hash mismatch" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted a hash-mismatched artifact")

    final_output_fixture = write_resume_fixture("transport-resume-final-output")
    write_text(final_output_fixture / "output.md", "already final\n")
    try:
        load_stage07_resume_context(root, final_output_fixture)
    except HarnessError as exc:
        if "existing final/assembly artifact" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted an existing final output")

    sidecar_fixture = write_resume_fixture("transport-resume-sidecar")
    sidecar_path = sidecar_fixture / "proof-sidecars" / "sidecar.json"
    write_json(sidecar_path, {"unexpected": True})
    try:
        load_stage07_resume_context(root, sidecar_fixture)
    except HarnessError as exc:
        if "downstream sidecars/promotion" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted existing sidecars")

    manifest_fixture = write_resume_fixture("transport-resume-manifest")
    manifest_context = load_stage07_resume_context(root, manifest_fixture)
    manifest_attempt_output = (
        manifest_fixture / "release-section-expansions" / "08-restorative-response-expansion-1-attempt-2.md"
    )
    write_text(manifest_attempt_output, "Successful resumed expansion.\n")
    manifest_attempt_log = (
        manifest_fixture / "responses" / "stage-07-release-output-08-restorative-response-expansion-1-attempt-2.codex-log.txt"
    )
    write_text(manifest_attempt_log, "ok\n")
    manifest_attempt_prompt = (
        manifest_fixture / "prompts" / "stage-07-release-output-08-restorative-response-expansion-1-attempt-2.prompt.md"
    )
    write_text(manifest_attempt_prompt, "Expand restorative response.\n")
    manifest_attempts = list(manifest_context["prior_attempts"])
    manifest_attempts.append(
        transport_attempt_record(
            root=root,
            subprocess_id=expansion_subprocess_id("restorative-response", 1),
            stage="stage-07-release-output",
            role="restorative_response",
            section_id="restorative-response",
            expansion_round=1,
            attempt=2,
            prompt_path=manifest_attempt_prompt,
            response_path=manifest_attempt_output,
            log_path=manifest_attempt_log,
            exit_code=0,
            status="pass",
            transport=classify_transport_failure(0, "ok\n"),
        )
    )
    manifest_attempts_record = manifest_fixture / "records" / "stage-07-transport-attempts.json"
    write_transport_attempts_record(manifest_attempts_record, root=root, attempts=manifest_attempts)
    manifest_path = manifest_fixture / "stage-07-output-assembly.manifest.json"
    write_compiled_release_manifest(
        root=root,
        manifest_path=manifest_path,
        case_name="self-test-transport-resume",
        raw_input_path=manifest_context["raw_input_path"],
        section_entries=[
            {
                "id": "restorative-response",
                "role": "restorative_response",
                "path": str(manifest_fixture / "release-sections" / "08-restorative-response.md"),
                "sha256": sha256_file(manifest_fixture / "release-sections" / "08-restorative-response.md"),
            }
        ],
        output_path=manifest_fixture / "output.md",
        per_burden_reread=[staged_output.self_test_per_burden_entry("B1")],
        transport_resume={
            "schema": TRANSPORT_RESUME_SCHEMA,
            "resumed": True,
            "source_run_dir": manifest_context["run_dir"],
            "failed_expansion": manifest_context["failed_expansion"],
            "attempts_record": rel(manifest_attempts_record, manifest_path.parent),
            "attempts": manifest_attempts,
        },
    )
    manifest_payload = load_json(manifest_path)
    if len(manifest_payload.get("transport_resume", {}).get("attempts", [])) != 2:
        raise HarnessError("Self-test resume manifest did not record failed and successful attempts")

    retry_fixture = run_dir / "transport-retry-budget"
    retry_fixture.mkdir(parents=True, exist_ok=True)
    retry_attempts: list[dict[str, Any]] = []
    retry_stage_files: list[Path] = []
    real_invoke_codex = invoke_codex

    def fake_transport_failure(
        _root: Path,
        _model: str,
        _prompt: str,
        _output_path: Path,
        log_path: Path,
    ) -> int:
        write_text(log_path, transport_log)
        return 1

    try:
        invoke_codex = fake_transport_failure
        try:
            invoke_expansion_with_transport_policy(
                root=root,
                model="fake-model",
                prompt="expand\n",
                base_prompt_path=retry_fixture / "call.prompt.md",
                base_output_path=retry_fixture / "call.md",
                base_log_path=retry_fixture / "call.codex-log.txt",
                section_id="restorative-response",
                section_role="restorative_response",
                expansion_round=1,
                first_attempt=1,
                retry_rounds=1,
                attempts=retry_attempts,
                attempts_record_path=retry_fixture / "stage-07-transport-attempts.json",
                stage_files=retry_stage_files,
            )
        except HarnessError as exc:
            if "transport retry budget exhausted after 2 attempt(s)" not in str(exc):
                raise
        else:
            raise HarnessError("Self-test retry budget did not stop after the bounded attempts")
    finally:
        invoke_codex = real_invoke_codex
    if len(retry_attempts) != 2:
        raise HarnessError("Self-test retry budget did not record exactly two attempts")
    normalized_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": {
                "token": "science-only-source-order-warrant",
                "basis": [
                    "scientific explanations treated as the only knowledge source",
                    "science-measurability treated as the criterion for whether an answer counts",
                ],
            },
            "live_registers": [
                {
                    "id": "xi",
                    "functions": ["warrant-authority", "source-order", "proof-tribunal"],
                    "basis": "science is installed as the only admissible knowledge source and criterion",
                },
                {
                    "id": "kappa",
                    "functions": ["dependency-collapse"],
                    "basis": "the only-science standard requires a self-grounding/dependency check before closure",
                },
            ],
            "burden_floor": [
                {
                    "burden_id": "B1",
                    "label": "science-only source-order/warrant standard",
                    "register_types": ["xi", "kappa"],
                }
            ],
        },
    )
    if normalized_stage02.get("selected_n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to normalize rich Stage 02 selected_n_frame into token")
    if normalized_stage02.get("live_registers") != ["xi", "kappa"]:
        raise HarnessError("Self-test failed to normalize rich Stage 02 live_registers into register ids")
    if normalized_stage02.get("burden_floor") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 02 burden_floor into burden-id list")
    if not isinstance(normalized_stage02.get("selected_n_frame_details"), dict):
        raise HarnessError("Self-test failed to preserve rich Stage 02 selected_n_frame details")
    if not isinstance(normalized_stage02.get("live_register_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 02 live register details")
    if not isinstance(normalized_stage02.get("burden_floor_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 02 burden-floor details")
    mixed_concealment_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "mixed-concealment-neutral-self-test",
            "held_n_frame_candidates": ["clarification-pressure-held", "refusal-pressure-held"],
            "live_registers": ["xi", "kappa"],
            "burden_floor": ["B1"],
            "diagnostic_ir_details": {
                "field": "MIXED NOETIC FIELD",
                "user_task": "REFUTE",
                "authority_frame": "LIVE",
                "claim_level": "neutral mixed concealment audit",
                "pattern_profile": "mixed source-owned concealment pressure",
                "do_orient": "neutral diagnostic pressure",
                "concealment_mode": (
                    "mixed - irad + juhud pressure; sincere clarification pressure routed to "
                    "clarification, not refusal; no hidden soul-state judgment"
                ),
                "deformation": "neutral mixed pressure before route release",
            },
        },
    )
    if mixed_concealment_stage02.get("diagnostic_ir_details", {}).get("concealment_mode", "").count("juhud") != 1:
        raise HarnessError("Self-test failed to preserve Stage 02 diagnostic_ir_details.concealment_mode")
    detail_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-bare-burden-floor-self-test",
            "live_registers": ["xi", "kappa"],
            "burden_floor": ["B1", "B2"],
            "burden_floor_details": [
                {
                    "burden_id": "B1",
                    "label": "source-order/warrant pressure",
                    "register_types": ["xi"],
                },
                {
                    "burden_id": "B2",
                    "label": "dependency-collapse pressure",
                    "register_types": ["kappa"],
                },
            ],
        },
    )
    if detail_stage02.get("burden_floor") != ["B1", "B2"]:
        raise HarnessError("Self-test failed to preserve bare Stage 02 burden_floor IDs")
    if not isinstance(detail_stage02.get("burden_floor_details"), list):
        raise HarnessError("Self-test failed to preserve Stage 02 burden_floor detail objects")
    keyed_detail_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-keyed-burden-detail-self-test",
            "live_registers": ["xi", "kappa"],
            "burden_floor": ["B1", "B2", "B3"],
            "burden_floor_details": {
                "B2": {
                    "label": "dependency-collapse pressure",
                    "register_types": ["kappa"],
                },
                "B1": {
                    "burden_id": "B1",
                    "label": "source-order/warrant pressure",
                    "register_types": ["xi"],
                },
                "B3": {
                    "id": "B3",
                    "label": "held proof-function pressure",
                    "register_types": ["xi", "kappa"],
                },
            },
        },
    )
    if keyed_detail_stage02.get("burden_floor") != ["B1", "B2", "B3"]:
        raise HarnessError("Self-test keyed Stage 02 details changed the burden floor")
    keyed_details = keyed_detail_stage02.get("burden_floor_details")
    if not isinstance(keyed_details, list) or [item.get("burden_id") for item in keyed_details] != ["B1", "B2", "B3"]:
        raise HarnessError("Self-test failed to normalize keyed Stage 02 burden details in floor order")
    keyed_registers = stage02_burden_register_types(keyed_detail_stage02, keyed_detail_stage02["burden_floor"])
    if keyed_registers.get("B2") != ["kappa"] or keyed_registers.get("B3") != ["xi", "kappa"]:
        raise HarnessError("Self-test keyed Stage 02 details lost register typing")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "selected-route-keyed-burden-detail-missing-self-test",
                "live_registers": ["xi", "kappa"],
                "burden_floor": ["B1", "B2", "B3"],
                "burden_floor_details": {
                    "B1": {"register_types": ["xi"]},
                    "B2": {"register_types": ["kappa"]},
                },
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject keyed Stage 02 details with missing burden")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "selected-route-keyed-burden-detail-mismatch-self-test",
                "live_registers": ["xi"],
                "burden_floor": ["B1"],
                "burden_floor_details": {
                    "B1": {"burden_id": "B2", "register_types": ["xi"]},
                },
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject keyed Stage 02 detail id mismatch")
    label_stage03 = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1", "B2"],
            "owner_routes": [
                {"burden_id": "B1", "owner_id": "source-status-repair"},
                {"burden_id": "B2", "owner_id": "M1"},
            ],
        },
    )
    validate_incremental_handoffs([detail_stage02, label_stage03])
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "selected-route-labeled-burden-floor-self-test",
                "live_registers": ["xi"],
                "burden_floor": ["B1: source-order/warrant pressure"],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 02 prose-labeled burden_floor string")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "selected-route-public-burden-floor-self-test",
                "live_registers": ["xi"],
                "burden_floor": ["¹B / ξ warrant-authority burden: selected source-authority pressure"],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 02 public/register/prose burden_floor string")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "selected-route-bad-burden-label-self-test",
                "live_registers": ["xi"],
                "burden_floor": ["source-order/warrant pressure without burden id"],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 02 burden_floor string without a canonical burden id")
    singular_detail_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-register-alias-self-test",
            "live_registers": ["xi", "sigma", "mu", "Omega", "kappa"],
            "burden_floor": ["B1", "B2", "B3", "B4"],
            "burden_floor_detail": [
                {"burden_id": "B1", "register_types": ["xi", "sigma"]},
                {"burden_id": "B2", "register_types": ["mu", "sigma"]},
                {"burden_id": "B3", "register_types": ["Omega"]},
                {"burden_id": "B4", "register_types": ["kappa"]},
            ],
        },
    )
    if not isinstance(singular_detail_stage02.get("burden_floor_details"), list):
        raise HarnessError("Self-test failed to promote singular Stage 02 burden_floor_detail alias")
    singular_coverage = stage02_register_coverage(singular_detail_stage02, singular_detail_stage02["burden_floor"])
    if singular_coverage.get("kappa") != ["B4"]:
        raise HarnessError("Self-test singular Stage 02 detail alias lost kappa coverage for B4")
    singular_registers = stage02_burden_register_types(singular_detail_stage02, singular_detail_stage02["burden_floor"])
    if singular_registers.get("B4") != ["kappa"]:
        raise HarnessError("Self-test singular Stage 02 detail alias lost B4 register typing")
    id_alias_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-id-alias-register-coverage-self-test",
            "live_registers": ["xi", "mu", "Omega", "kappa"],
            "burden_floor": ["B1", "B2", "B3"],
            "burden_floor_details": [
                {"id": "B1", "register_types": ["xi", "mu"]},
                {"id": "B2", "register_types": ["Omega"]},
                {"id": "B3", "register_types": ["kappa"]},
            ],
        },
    )
    id_alias_coverage = stage02_register_coverage(id_alias_stage02, id_alias_stage02["burden_floor"])
    if id_alias_coverage.get("kappa") != ["B3"]:
        raise HarnessError("Self-test Stage 02 id alias lost kappa diagnostic coverage for B3")
    id_alias_registers = stage02_burden_register_types(id_alias_stage02, id_alias_stage02["burden_floor"])
    if id_alias_registers.get("B3") != ["kappa"]:
        raise HarnessError("Self-test Stage 02 id alias lost B3 kappa register typing")
    worldview_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-worldview-register-coverage-self-test",
            "live_registers": ["ontology", "authority"],
            "burden_floor": ["B1", "B2"],
            "burden_floor_details": [
                {
                    "id": "B1",
                    "canonical_role": "define_target_claim",
                    "diagnostic_note": "Secularism must be specified as a worldview or governing public reason claim before refutation can proceed.",
                },
                {
                    "id": "B2",
                    "canonical_role": "identify_authority_and_warrant",
                    "diagnostic_note": "The live pressure concerns what source licenses authority when revelation is excluded or privatized.",
                },
            ],
        },
    )
    worldview_coverage = stage02_register_coverage(worldview_stage02, worldview_stage02["burden_floor"])
    if worldview_coverage.get("Omega") != ["B1"]:
        raise HarnessError("Self-test Stage 02 worldview detail lost Omega diagnostic coverage for B1")
    if "mu" in worldview_coverage:
        raise HarnessError("Self-test Stage 02 worldview detail treated the word 'must' as mu coverage")
    worldview_registers = stage02_public_live_registers(worldview_stage02, worldview_stage02["burden_floor"])
    if worldview_registers != ["Omega", "xi"]:
        raise HarnessError("Self-test Stage 02 worldview live registers did not normalize to Omega/xi")
    partial_register_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-partial-register-coverage-self-test",
            "live_registers": ["definition", "epistemology", "metaphysics"],
            "burden_floor": ["B1", "B2", "B3"],
            "burden_floor_details": [
                {"id": "B1", "label": "definition_and_scope"},
                {
                    "id": "B2",
                    "label": "epistemic_authority",
                    "diagnostic_role": "Test whether the governing knowledge standard has authority.",
                },
                {"id": "B3", "label": "normative_grounding"},
            ],
        },
    )
    partial_register_coverage = stage02_register_coverage(
        partial_register_stage02,
        partial_register_stage02["burden_floor"],
    )
    if partial_register_coverage.get("Omega") != ["B3"]:
        raise HarnessError("Self-test Stage 02 partial detail coverage lost live-register Omega fallback for B3")
    partial_register_types = stage02_burden_register_types(
        partial_register_stage02,
        partial_register_stage02["burden_floor"],
    )
    if partial_register_types.get("B3") != ["Omega"]:
        raise HarnessError("Self-test Stage 02 partial detail coverage lost B3 Omega register typing")
    registers_alias_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "selected-route-register-detail-alias-self-test",
            "live_registers": ["m", "tau", "sigma", "xi", "Omega", "mu", "kappa"],
            "burden_floor": ["B1", "B2", "B3", "B4"],
            "burden_floor_details": [
                {"burden_id": "B1", "registers": ["m", "tau", "Omega"]},
                {"burden_id": "B2", "registers": ["xi", "sigma"]},
                {"burden_id": "B3", "registers": ["mu", "tau"]},
                {"burden_id": "B4", "registers": ["kappa", "Omega"]},
            ],
        },
    )
    registers_alias_coverage = stage02_register_coverage(registers_alias_stage02, registers_alias_stage02["burden_floor"])
    for register, expected_burdens in {
        "Omega": ["B1", "B4"],
        "mu": ["B3"],
        "kappa": ["B4"],
    }.items():
        if registers_alias_coverage.get(register) != expected_burdens:
            raise HarnessError(
                f"Self-test Stage 02 registers alias lost {register} coverage: {registers_alias_coverage.get(register)}"
            )
    registers_alias_burden_types = stage02_burden_register_types(
        registers_alias_stage02,
        registers_alias_stage02["burden_floor"],
    )
    if registers_alias_burden_types.get("B4") != ["kappa", "Omega"]:
        raise HarnessError("Self-test Stage 02 registers alias lost B4 kappa/Omega typing")
    legacy_register_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": "legacy-register-projection-self-test",
            "live_registers": [
                "scriptural-text",
                "source-order",
                "predication",
                "entailment",
            ],
            "burden_floor": ["B1", "B2"],
            "burden_floor_details": [
                {
                    "id": "B1",
                    "pressure": "exclusive predication and person-nature pressure",
                    "why_live": "the predicate and nature relation are load-bearing",
                },
                {
                    "id": "B2",
                    "pressure": "source-order and entailment/backread pressure",
                    "why_live": "the downstream entailment chain is load-bearing",
                },
            ],
        },
    )
    legacy_live = stage02_public_live_registers(legacy_register_stage02, legacy_register_stage02["burden_floor"])
    if legacy_live != ["xi", "Omega", "kappa"]:
        raise HarnessError(f"Self-test legacy Stage 02 register projection drifted: {legacy_live}")
    legacy_coverage = stage02_register_coverage(legacy_register_stage02, legacy_register_stage02["burden_floor"])
    if legacy_coverage.get("kappa") != ["B2"]:
        raise HarnessError("Self-test legacy Stage 02 entailment pressure did not project to kappa coverage for B2")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": {"basis": ["missing token"]},
                "live_registers": [{"id": "xi"}],
                "burden_floor": [{"burden_id": "B1"}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject rich Stage 02 selected_n_frame without token")

    normalized = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": [
                {
                    "burden_id": "B1",
                    "route_target": "science-only-source-order-warrant",
                    "register_types": ["xi", "kappa"],
                }
            ],
            "owner_routes": [{"burden_id": "B1", "owner_id": "source-status-repair"}],
        },
    )
    if normalized.get("route_targets") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 03 route_targets into burden-id list")
    if not isinstance(normalized.get("route_target_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 03 route metadata")
    normalized_owner_routes = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "target": "B1",
                    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
                    "classification": "required_owner_sequence",
                    "required": [
                        {
                            "owner": "source-status-repair",
                            "operation": "source-order",
                            "pressure_label": "scientific-explanations-only-knowledge-source",
                        },
                        {
                            "owner": "M1",
                            "operation": "self-grounding-test",
                            "pressure_label": "only-science-counts-standard",
                        },
                    ],
                }
            ],
        },
    )
    if normalized_owner_routes.get("owner_routes") != [
        {
            "burden_id": "B1",
            "owner_id": "source-status-repair",
            "operation": "source-order",
            "eligibility": "required_owner_sequence",
        },
        {
            "burden_id": "B1",
            "owner_id": "M1",
            "operation": "self-grounding-test",
            "eligibility": "required_owner_sequence",
        },
    ]:
        raise HarnessError("Self-test failed to normalize rich Stage 03 owner_routes into owner identities")
    if not isinstance(normalized_owner_routes.get("owner_route_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 03 owner-route details")
    normalized_alias_owner_routes = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "burden_id": "B1",
                    "owner_id": "PROOF_METHOD",
                    "operation": "proof-family-and-carrier-audit",
                }
            ],
        },
    )
    alias_route = normalized_alias_owner_routes.get("owner_routes", [{}])[0]
    if alias_route.get("owner_id") != "proof-method-audit":
        raise HarnessError("Self-test failed to canonicalize PROOF_METHOD Stage 03 owner route")
    if alias_route.get("classification_family") != "PROOF_METHOD":
        raise HarnessError("Self-test failed to preserve PROOF_METHOD as route classification metadata")
    alias_events = (normalized_alias_owner_routes.get("normalization") or {}).get("owner_route_family_aliases")
    if not isinstance(alias_events, list) or not alias_events:
        raise HarnessError("Self-test failed to record PROOF_METHOD owner-route alias normalization")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [{"target": "B1", "required": [{}]}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject rich Stage 03 owner route without owner id")
    normalized_m9_route = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "burden_id": "B1",
                    "owner_id": "M9",
                    "operation": "predication-repair",
                    "route_status": "executable",
                }
            ],
        },
    )
    if normalized_m9_route.get("owner_routes") != [
        {
            "burden_id": "B1",
            "owner_id": "M9",
            "operation": "predication-repair",
            "route_status": "executable",
        }
    ]:
        raise HarnessError("Self-test failed to accept controlled M9 Stage 03 operation")
    normalized_m9_result_operation_route = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B3"],
            "owner_routes": [
                {
                    "burden_id": "B3",
                    "owner_id": "M9",
                    "operation": "referent-separated",
                    "owner_operation": "referent-separated",
                    "pressure": "proof-text-referent-and-predicate-function",
                    "delta_result": "referent-separated",
                }
            ],
        },
    )
    normalized_m9_result_operation_row = normalized_m9_result_operation_route["owner_routes"][0]
    if (
        normalized_m9_result_operation_row.get("operation") != "predication-repair"
        or normalized_m9_result_operation_row.get("owner_operation") != "predication-repair"
    ):
        raise HarnessError("Self-test failed to normalize M9 result token in operation slot")
    result_operation_events = (
        normalized_m9_result_operation_route.get("normalization") or {}
    ).get("owner_route_operation_result_tokens")
    if not isinstance(result_operation_events, list) or not result_operation_events:
        raise HarnessError("Self-test failed to record M9 result-token operation normalization")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [
                    {
                        "burden_id": "B1",
                        "owner_id": "M9",
                        "operation": "predication-mode",
                        "route_status": "executable",
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "operation token 'predication-mode' is outside controlled operation vocabulary for M9" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted M9 mode label as an executable Stage 03 operation")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [
                    {
                        "burden_id": "B1",
                        "owner_id": "source-status-repair",
                        "operation": "source-status-repair.source-order",
                        "route_status": "executable",
                    }
                ],
            },
        )
    except HarnessError as exc:
        if (
            "operation token 'source-status-repair.source-order' is outside controlled operation "
            "vocabulary for SOURCE"
            not in str(exc)
        ):
            raise
    else:
        raise HarnessError("Self-test accepted prefixed owner alias as a Stage 03 operation token")

    normalized_p7_family_hint_route = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "burden_id": "B1",
                    "owner_id": "scope-boundary",
                    "owner_family": "P7",
                    "operation": "scope-boundary",
                    "owner_operation": "scope-boundary",
                    "route_status": "executable",
                }
            ],
        },
    )
    p7_hint_route = normalized_p7_family_hint_route.get("owner_routes", [{}])[0]
    if p7_hint_route.get("owner_id") != "P7":
        raise HarnessError("Self-test failed to canonicalize P7 operation token owner_id from owner_family")
    p7_hint_events = (normalized_p7_family_hint_route.get("normalization") or {}).get("owner_route_family_hints")
    if not isinstance(p7_hint_events, list) or not p7_hint_events:
        raise HarnessError("Self-test failed to record P7 owner-family hint normalization")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [
                    {
                        "burden_id": "B1",
                        "owner_id": "scope-boundary",
                        "operation": "scope-boundary",
                        "route_status": "executable",
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "executable owner route 'scope-boundary' has no controlled owner family" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted operation token as owner_id without owner_family evidence")

    normalized_m8_dependency_route = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "burden_id": "B1",
                    "owner_id": "M8",
                    "operation": "dependency-trace",
                    "delta_result_vocabulary": ["dependency-exposed"],
                    "route_status": "executable",
                }
            ],
        },
    )
    if normalized_m8_dependency_route.get("owner_routes") != [
        {
            "burden_id": "B1",
            "owner_id": "M8",
            "operation": "dependency-trace",
            "delta_result_vocabulary": ["dependency-exposed"],
            "route_status": "executable",
        }
    ]:
        raise HarnessError("Self-test failed to accept M8 dependency-trace operation-specific delta floor")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [
                    {
                        "burden_id": "B1",
                        "owner_id": "M8",
                        "operation": "dependency-trace",
                        "delta_result_vocabulary": ["dependency-exposed", "entailment-blocked"],
                        "route_status": "executable",
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "M8.dependency-trace requires operation-specific delta_result 'dependency-exposed'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted broad M8 dependency-trace delta_result vocabulary")

    normalized_m1p_route = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "burden_id": "B1",
                    "owner_id": "M1-P",
                    "operation": "performative-test",
                    "route_status": "executable",
                }
            ],
        },
    )
    if normalized_m1p_route.get("owner_routes") != [
        {
            "burden_id": "B1",
            "owner_id": "M1-P",
            "operation": "performative-test",
            "route_status": "executable",
        }
    ]:
        raise HarnessError("Self-test failed to accept controlled M1-P Stage 03 operation")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [
                    {
                        "burden_id": "B1",
                        "owner_id": "M1-P",
                        "operation": "authority-premise-test",
                        "route_status": "executable",
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "operation token 'authority-premise-test' is outside controlled operation vocabulary for M1-P" not in str(
            exc
        ):
            raise
    else:
        raise HarnessError("Self-test accepted authority/source pressure as an M1-P Stage 03 operation")

    stage03_guidance = stage03_owner_operation_guidance()
    for required in (
        "delta/register family codes are observations, not executable owner ids",
        "Stage 03 owner_id mapping: `DO_SECOND_LOOP` -> `do-second-loop`",
        "use `do-second-loop` in `owner_routes[].owner_id`, not `DO_SECOND_LOOP`",
        "Stage 03 owner_id mapping: `PROOF_METHOD` -> `proof-method-audit`",
        "use `proof-method-audit` in `owner_routes[].owner_id`, not `PROOF_METHOD`",
        "Stage 03 owner_id mapping: `PATTERN_PROFILE` -> `pattern-profiling`",
        "`authority-order-repair` for authority, rank, tribunal",
        "`source-order-repair` only for source lineage, quotation chain",
    ):
        if required not in stage03_guidance:
            raise HarnessError(f"Self-test Stage 03 owner guidance omitted {required}")

    canonical_act_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
    )

    def self_test_act_row_details(rows: list[str], axis_by_ref: dict[str, str]) -> list[dict[str, str]]:
        details: list[dict[str, str]] = []
        for row in rows:
            parsed = parsed_stage04_act_detail(row)
            if not parsed:
                raise HarnessError("Self-test fixture contains an unparseable Stage 04 ACT row")
            ref = parsed["body_ref"]
            axis = axis_by_ref.get(ref)
            if not axis:
                raise HarnessError(f"Self-test fixture missing register axis for {ref}")
            details.append(
                {
                    "burden_id": parsed["burden_id"],
                    "body_ref": ref,
                    "owner_id": parsed["owner_id"],
                    "operation": parsed["operation"],
                    "register_axis": axis,
                    "delta_result": parsed["delta_result"],
                    "act_row": row,
                }
            )
        return details

    registers_alias_act_rows = [
        (
            "⟦ACT ¹B₁[M9.predication-repair] :: "
            "π=selected-model-predication-pressure :: body_ref=¹B₁ :: "
            "Δ=Δ¹B:person-nature-transfer-blocked :: Land(¹B)+⟧"
        ),
        (
            "⟦ACT ²B₁[source-status-repair.source-order] :: "
            "π=source-order-pressure :: body_ref=²B₁ :: "
            "Δ=Δ²B:proof-text-sorted :: Land(²B)+⟧"
        ),
        (
            "⟦ACT ³B₁[M7.definition-anchor] :: "
            "π=semantic-compression-pressure :: body_ref=³B₁ :: "
            "Δ=Δ³B:semantic-anchor-stabilized :: Land(³B)+⟧"
        ),
        (
            "⟦ACT ⁴B₁[M8.dependency-trace] :: "
            "π=dependency-collapse-pressure :: body_ref=⁴B₁ :: "
            "Δ=Δκ:dependency-exposed :: Land(⁴B)+⟧"
        ),
    ]
    registers_alias_stage07_contract = stage07_field_witness_contract_guidance(
        [
            registers_alias_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1", "B2", "B3", "B4"],
                "act_burdens": ["B1", "B2", "B3", "B4"],
                "act_rows": registers_alias_act_rows,
            },
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "terminal_states": {"B1": "landed", "B2": "landed", "B3": "landed", "B4": "landed"},
                "reread_state": {"source_burden": "B4", "route_result_type": "no_new_resultant", "route": "STOP"},
                "per_burden_reread": [
                    self_test_reread_entry("B1"),
                    self_test_reread_entry("B2"),
                    self_test_reread_entry("B3"),
                    self_test_reread_entry("B4"),
                ],
            },
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "selected_n_frame": "selected-route-register-detail-alias-self-test",
                "live_registers": ["m", "tau", "sigma", "xi", "Omega", "mu", "kappa"],
                "register_deltas": {
                    "Omega": ["person-nature-transfer-blocked"],
                    "mu": ["semantic-anchor-stabilized"],
                    "kappa": ["dependency-exposed"],
                },
            },
        ]
    )
    for register, expected_pattern in {
        "Omega": r'"Omega": \[\s*"B1",\s*"B4"\s*\]',
        "mu": r'"mu": \[\s*"B3"\s*\]',
        "kappa": r'"kappa": \[\s*"B4"\s*\]',
    }.items():
        if not re.search(expected_pattern, registers_alias_stage07_contract):
            raise HarnessError(f"Self-test Stage 07 scaffold lost Stage 02 `registers` coverage for {register}")
    if not re.search(r'"register_types": \[\s*"kappa",\s*"Omega"\s*\]', registers_alias_stage07_contract):
        raise HarnessError("Self-test Stage 07 scaffold lost node register_types copied from Stage 02 `registers`")

    normalized_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [
                {
                    "burden_id": "B1",
                    "body_ref": "¹B₁",
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "register_axis": "σ",
                    "delta_result": "science-source-bounded",
                    "act_row": canonical_act_row,
                }
            ],
        },
    )
    if normalized_stage04.get("act_rows") != [canonical_act_row]:
        raise HarnessError("Self-test failed to normalize Stage 04 object-shaped act_rows into strings")
    if normalized_stage04.get("act_body_refs") != ["¹B₁"]:
        raise HarnessError("Self-test failed to derive Stage 04 act_body_refs from canonical ACT rows")
    if not isinstance(normalized_stage04.get("act_row_details"), list):
        raise HarnessError("Self-test failed to preserve Stage 04 act_row_details")
    alias_operation_rows = [
        "⟦ACT ¹B₁[M8.trace] :: π=time-sequence-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:consequence-traced :: Land(¹B)+⟧",
        "⟦ACT ¹B₂[P7.boundary] :: π=completion-boundary-pressure :: body_ref=¹B₂ :: Δ=Δ¹B:scope-boundary-named :: Land(¹B)+⟧",
    ]
    alias_operation_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁", "¹B₂"],
            "act_rows": alias_operation_rows,
            "act_row_details": self_test_act_row_details(
                alias_operation_rows,
                {"¹B₁": "κ", "¹B₂": "σ"},
            ),
        },
    )
    if "[M8.consequence-trace]" not in alias_operation_stage04["act_rows"][0]:
        raise HarnessError("Self-test failed to canonicalize Stage 04 M8.trace alias")
    if "[P7.scope-boundary]" not in alias_operation_stage04["act_rows"][1]:
        raise HarnessError("Self-test failed to canonicalize Stage 04 P7.boundary alias")
    if alias_operation_stage04["act_row_details"][0].get("operation") != "consequence-trace":
        raise HarnessError("Self-test failed to canonicalize Stage 04 M8 trace detail")
    if alias_operation_stage04["act_row_details"][1].get("operation") != "scope-boundary":
        raise HarnessError("Self-test failed to canonicalize Stage 04 P7 boundary detail")
    do_second_loop_axis_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1", "B2", "B3", "B4"],
            "act_burdens": ["B1", "B2", "B3", "B4"],
            "act_body_refs": ["¹B₁", "²B₁", "³B₁", "⁴B₁"],
            "act_rows": [
                (
                    "⟦ACT ¹B₁[do-second-loop.punishment-proportionality-accountability] :: "
                    "π=punishment-proportionality-pressure :: body_ref=¹B₁ :: "
                    "Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧"
                ),
                (
                    "⟦ACT ²B₁[do-second-loop.coercive-guidance-demand] :: "
                    "π=coercive-guidance-demand :: body_ref=²B₁ :: "
                    "Δ=Δ²B:coercive-guidance-demand-bounded :: Land(²B)+⟧"
                ),
                (
                    "⟦ACT ³B₁[do-second-loop.fitrah-ayat-baseline] :: "
                    "π=fitrah-ayat-baseline :: body_ref=³B₁ :: "
                    "Δ=Δ³B:fitrah-ayat-baseline-established :: Land(³B)+⟧"
                ),
                (
                    "⟦ACT ⁴B₁[do-second-loop.accountability-hujjah-compression] :: "
                    "π=accountability-hujjah-compression :: body_ref=⁴B₁ :: "
                    "Δ=Δ⁴B:accountability-hujjah-narrowed :: Land(⁴B)+⟧"
                ),
            ],
            "act_row_details": [
                {
                    "act_row": (
                        "⟦ACT ¹B₁[do-second-loop.punishment-proportionality-accountability] :: "
                        "π=punishment-proportionality-pressure :: body_ref=¹B₁ :: "
                        "Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧"
                    ),
                    "body_ref": "¹B₁",
                    "burden_id": "B1",
                    "owner_id": "do-second-loop",
                    "operation": "punishment-proportionality-accountability",
                    "register_axis": "m",
                    "delta_result": "punishment-proportionality-calibrated",
                },
                {
                    "act_row": (
                        "⟦ACT ²B₁[do-second-loop.coercive-guidance-demand] :: "
                        "π=coercive-guidance-demand :: body_ref=²B₁ :: "
                        "Δ=Δ²B:coercive-guidance-demand-bounded :: Land(²B)+⟧"
                    ),
                    "body_ref": "²B₁",
                    "burden_id": "B2",
                    "owner_id": "do-second-loop",
                    "operation": "coercive-guidance-demand",
                    "register_axis": "τ",
                    "delta_result": "coercive-guidance-demand-bounded",
                },
                {
                    "act_row": (
                        "⟦ACT ³B₁[do-second-loop.fitrah-ayat-baseline] :: "
                        "π=fitrah-ayat-baseline :: body_ref=³B₁ :: "
                        "Δ=Δ³B:fitrah-ayat-baseline-established :: Land(³B)+⟧"
                    ),
                    "body_ref": "³B₁",
                    "burden_id": "B3",
                    "owner_id": "do-second-loop",
                    "operation": "fitrah-ayat-baseline",
                    "register_axis": "N",
                    "delta_result": "fitrah-ayat-baseline-established",
                },
                {
                    "act_row": (
                        "⟦ACT ⁴B₁[do-second-loop.accountability-hujjah-compression] :: "
                        "π=accountability-hujjah-compression :: body_ref=⁴B₁ :: "
                        "Δ=Δ⁴B:accountability-hujjah-narrowed :: Land(⁴B)+⟧"
                    ),
                    "body_ref": "⁴B₁",
                    "burden_id": "B4",
                    "owner_id": "do-second-loop",
                    "operation": "accountability-hujjah-compression",
                    "register_axis": "H",
                    "delta_result": "accountability-hujjah-narrowed",
                },
            ],
        },
    )
    if do_second_loop_axis_stage04["act_row_details"][0].get("register_axis") != "♥":
        raise HarnessError("Self-test failed to canonicalize do-second-loop punishment register_axis fallback")
    if do_second_loop_axis_stage04["act_row_details"][1].get("register_axis") != "κ":
        raise HarnessError("Self-test failed to canonicalize do-second-loop guidance register_axis fallback")
    if do_second_loop_axis_stage04["act_row_details"][2].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to canonicalize do-second-loop fitrah/ayat register_axis fallback")
    if do_second_loop_axis_stage04["act_row_details"][3].get("register_axis") != "κ":
        raise HarnessError("Self-test failed to canonicalize do-second-loop hujjah/accountability register_axis fallback")
    do_second_loop_tau_punishment_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [
                (
                    "⟦ACT ¹B₁[do-second-loop.punishment-proportionality-accountability] :: "
                    "π=punishment-proportionality :: body_ref=¹B₁ :: "
                    "Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧"
                )
            ],
            "act_row_details": [
                {
                    "act_row": (
                        "⟦ACT ¹B₁[do-second-loop.punishment-proportionality-accountability] :: "
                        "π=punishment-proportionality :: body_ref=¹B₁ :: "
                        "Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧"
                    ),
                    "body_ref": "¹B₁",
                    "burden_id": "B1",
                    "owner_id": "do-second-loop",
                    "operation": "punishment-proportionality-accountability",
                    "register_axis": "τ",
                    "delta_result": "punishment-proportionality-calibrated",
                }
            ],
        },
    )
    if do_second_loop_tau_punishment_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to accept do-second-loop punishment τ register_axis")
    do_second_loop_h_guidance_row = (
        "⟦ACT ¹B₁[do-second-loop.coercive-guidance-demand] :: "
        "π=coercive-guidance-demand :: body_ref=¹B₁ :: "
        "Δ=Δ¹B:coercive-guidance-demand-bounded :: Land(¹B)+⟧"
    )
    do_second_loop_h_guidance_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [do_second_loop_h_guidance_row],
            "act_row_details": self_test_act_row_details([do_second_loop_h_guidance_row], {"¹B₁": "H"}),
        },
    )
    if do_second_loop_h_guidance_stage04["act_row_details"][0].get("register_axis") != "κ":
        raise HarnessError("Self-test failed to canonicalize do-second-loop H guidance register_axis fallback")
    validate_incremental_handoffs(
        [
            {
                "id": "stage-03-routing-owner-gate",
                "status": "partial",
                "route_targets": ["B1", "B2"],
            },
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "held_act_targets": ["B2"],
            },
        ]
    )
    try:
        validate_incremental_handoffs(
            [
                {
                    "id": "stage-03-routing-owner-gate",
                    "status": "partial",
                    "route_targets": ["B1", "B2"],
                },
                {
                    "id": "stage-04-burden-execution-act",
                    "status": "pass",
                    "act_targets": ["B1"],
                },
            ]
        )
    except HarnessError as exc:
        if "route_targets must be covered by act_targets or held_act_targets" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted Stage 04 route target missing from ACT and held coverage")
    missing_slot_separators_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] "
        "body_ref=¹B₁ π=scientific-explanations-only-knowledge-source "
        "Δ=Δ¹B:science-source-bounded Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁"],
                "act_rows": [missing_slot_separators_row],
                "act_row_details": [
                    {
                        "burden_id": "B1",
                        "body_ref": "¹B₁",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": missing_slot_separators_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "act_rows[0] is not a parseable canonical ACT row" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject Stage 04 ACT row without canonical slot separators")
    hydrated_missing_body_ref = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [canonical_act_row],
            "act_row_details": [
                {
                    "burden_id": "B1",
                    "body_ref": None,
                    "owner_id": "source-status-repair",
                    "operation": None,
                    "register_axis": "sigma",
                    "delta_result": "science-source-bounded",
                    "act_row": canonical_act_row,
                }
            ],
        },
    )
    hydrated_detail = hydrated_missing_body_ref["act_row_details"][0]
    if hydrated_detail.get("body_ref") != "¹B₁" or hydrated_detail.get("operation") != "source-order":
        raise HarnessError("Self-test failed to hydrate Stage 04 act_row_details from ACT row text")
    hydrated_missing_burden = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [canonical_act_row],
            "act_row_details": [
                {
                    "burden_id": None,
                    "body_ref": "¹B₁",
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "register_axis": "σ",
                    "delta_result": "science-source-bounded",
                    "act_row": canonical_act_row,
                }
            ],
        },
    )
    if hydrated_missing_burden["act_row_details"][0].get("burden_id") != "B1":
        raise HarnessError("Self-test failed to hydrate Stage 04 act_row_details burden_id from Land()")
    multi_b1_rows = [
        (
            f"⟦ACT {ref}[source-status-repair.source-order] :: "
            "π=scientific-explanations-only-knowledge-source :: "
            f"body_ref={ref} :: Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
        )
        for ref in ("¹B₁", "¹B₂", "¹B₃")
    ]
    accepted_multi_b1_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁", "¹B₂", "¹B₃"],
            "act_rows": multi_b1_rows,
            "act_row_details": [
                {
                    "burden_id": "B1",
                    "body_ref": ref,
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "register_axis": "σ",
                    "delta_result": "science-source-bounded",
                    "act_row": row,
                }
                for ref, row in zip(("¹B₁", "¹B₂", "¹B₃"), multi_b1_rows, strict=True)
            ],
        },
    )
    if accepted_multi_b1_stage04.get("act_body_refs") != ["¹B₁", "¹B₂", "¹B₃"]:
        raise HarnessError("Self-test failed to accept unambiguous B1 submove body_ref sequence")
    swapped_axis_b1_row = (
        "⟦ACT ²B₁[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=²B₁ :: Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁", "²B₁"],
                "act_rows": [multi_b1_rows[0], swapped_axis_b1_row],
                "act_row_details": [
                    {
                        "burden_id": "B1",
                        "body_ref": "¹B₁",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": multi_b1_rows[0],
                    },
                    {
                        "burden_id": "B1",
                        "body_ref": "²B₁",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": swapped_axis_b1_row,
                    },
                ],
            },
        )
    except HarnessError as exc:
        if "body_ref '²B₁' encodes B2 but Land() targets B1" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject Stage 04 body_ref burden/submove axis swap")
    owner_qualified_body_ref_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=¹B₁[source-status-repair.source-order] :: "
        "Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁[source-status-repair.source-order]"],
                "act_rows": [owner_qualified_body_ref_row],
                "act_row_details": [
                    {
                        "burden_id": "B1",
                        "body_ref": "¹B₁[source-status-repair.source-order]",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": owner_qualified_body_ref_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "owner.operation belongs in ACT bracket/object fields, not body_ref" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject owner-qualified Stage 04 body_ref fields")
    accepted_layer_separated_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [canonical_act_row],
            "act_row_details": [
                {
                    "burden_id": "B1",
                    "body_ref": "¹B₁",
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "register_axis": "sigma",
                    "register_name": "source_status",
                    "delta_result": "science-source-bounded",
                    "act_row": canonical_act_row,
                }
            ],
        },
    )
    if accepted_layer_separated_stage04["act_row_details"][0].get("register_axis") != "σ":
        raise HarnessError("Self-test failed to accept separate source-status register_axis")
    mismatched_owner_body_ref_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=¹B₁[M9.predication-repair] :: "
        "Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁[M9.predication-repair]"],
                "act_rows": [mismatched_owner_body_ref_row],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "register_axis": "μ",
                        "delta_result": "science-source-bounded",
                        "act_row": mismatched_owner_body_ref_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "owner.operation belongs in ACT bracket/object fields, not body_ref" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject mismatched owner-qualified Stage 04 body_ref")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁[M9.predication-repair]"],
                "act_rows": [canonical_act_row],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": canonical_act_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "owner.operation belongs in owner_id/operation fields" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject untied owner-qualified Stage 04 act_body_refs")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁"],
                "act_rows": [canonical_act_row],
                "act_row_details": [
                    {
                        "burden_id": "B1",
                        "body_ref": "²B₁",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "register_axis": "σ",
                        "delta_result": "science-source-bounded",
                        "act_row": canonical_act_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "body_ref disagrees" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject conflicting Stage 04 act_row_details body_ref")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["¹B₁"],
                "act_rows": [canonical_act_row],
                "act_row_details": ["B1: prose summary is not handoff evidence"],
            },
        )
    except HarnessError as exc:
        if "act_row_details[0] must be an object" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject prose string Stage 04 act_row_details")
    mismatched_head_body_ref_row = (
        "⟦ACT B1[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=B1.source-status-repair.source-order :: Δ=ΔB1:science-source-bounded :: Land(B1)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_body_refs": ["B1.source-status-repair.source-order"],
                "act_rows": [mismatched_head_body_ref_row],
                "act_row_details": [{"act_row": mismatched_head_body_ref_row}],
            },
        )
    except HarnessError as exc:
        if "act_rows[0] is not a parseable canonical ACT row" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject Stage 04 ACT head/body_ref dialect mismatch")
    selected_model_delta_guidance = stage04_delta_vocabulary_guidance(
        [
            {
                "id": "stage-03-routing-owner-gate",
                "owner_routes": [
                    {"burden_id": "B1", "owner_id": "do-christian-extensions"},
                    {"burden_id": "B1", "owner_id": "M9"},
                    {"burden_id": "B2", "owner_id": "M7"},
                    {"burden_id": "B2", "owner_id": "M3"},
                    {"burden_id": "B2", "owner_id": "M9"},
                    {"burden_id": "B3", "owner_id": "source-status-repair"},
                    {"burden_id": "B3", "owner_id": "authority-order-repair"},
                    {"burden_id": "B4", "owner_id": "M8"},
                    {"burden_id": "B4", "owner_id": "M9"},
                    {"burden_id": "B5", "owner_id": "proof-method-audit"},
                    {"burden_id": "B6", "owner_id": "V2.reconstituting-reason"},
                    {"burden_id": "B7", "owner_id": "pattern-profiling"},
                    {"burden_id": "B8", "owner_id": "unmapped-neutral-owner"},
                ],
            }
        ]
    )
    for required in (
        "The token after the dot in `[owner.operation]` must be one of the source-owned owner-local operation tokens below",
        "DO_CHRISTIAN: fan-out-route-named, trinitarian-model-identified",
        "DO_CHRISTIAN is a delta/register vocabulary family for callable owner `do-christian-extensions`",
        "DO_CHRISTIAN operations: model-identification",
        "M7: definition-anchored",
        "M3 operations: orphaned-intuition",
        "M3: grounding-severed",
        "M8: coercive-clarity-entailment-demoted",
        "M8 operation-specific delta floor: `dependency-trace` requires `dependency-exposed`",
        "M9 operations: predication-repair, sense-split",
        "M9: category-separated",
        "M9 delta_result tokens such as `predicate-separated`, `category-separated`, `referent-separated`, and `sense-separated` are not callable operations",
        "PROOF_METHOD operations: proof-denominator-audit, proof-family-and-carrier-audit",
        "PROOF_METHOD is a delta/register vocabulary family for callable owner `proof-method-audit`",
        "PROOF_METHOD: proof-denominator-exposed",
        "SOURCE operations: authority-order-repair, sort, source-order, source-order-repair",
        "SOURCE: authority-order-repaired",
        "SOURCE register-axis floor: authority-order/source-status repairs act on source/semantic/authority status (`σ`)",
        "V2 operations: proof-burden-order, reason-role-repair, reconstituting-reason",
        "V2: frame-cleared",
        "PATTERN_PROFILE operations: collapse-radius-mapping, loaded-label-carrier-audit, mutation-after-challenge-tracking, pattern-profile, proof-packet-reconstruction",
        "PATTERN_PROFILE is a delta/register vocabulary family for callable owner `pattern-profiling`",
        "PATTERN_PROFILE: carrier-function-typed",
        "Routed owners without controlled Stage 04 operation/delta_result vocabulary: unmapped-neutral-owner",
        "controlled-vocabulary-gap evidence",
        "Tokens are family-local proof terms",
        "For M9 predication/identity pressure, use an M9 token such as `predicate-separated`",
        "Do not invent near-synonyms such as `predicate-transfer-blocked`",
    ):
        if required not in selected_model_delta_guidance:
            raise HarnessError(f"Self-test Stage 04 delta vocabulary guidance omitted {required}")
    if "M9 operations: category-or-referent-separation" in selected_model_delta_guidance:
        raise HarnessError("Self-test Stage 04 guidance laundered an M9 delta/result label into operation space")
    if "SOURCE operations: authority-order-repair, sort, source-order, source-order-repair, status" in selected_model_delta_guidance:
        raise HarnessError("Self-test Stage 04 guidance exposed SOURCE status as a callable operation")
    m3_orphaned_row = (
        "⟦ACT ¹B₁[M3.orphaned-intuition] :: "
        "π=moral-recognition-grounding-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:normativity-restored-to-ground :: Land(¹B)+⟧"
    )
    m3_orphaned_m_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [m3_orphaned_row],
            "act_row_details": self_test_act_row_details([m3_orphaned_row], {"¹B₁": "m"}),
        },
    )
    if m3_orphaned_m_stage04["act_row_details"][0].get("register_axis") != "♥":
        raise HarnessError("Self-test failed to canonicalize M3 orphaned-intuition m fallback to heart axis")
    do_second_loop_guidance = stage04_delta_vocabulary_guidance(
        [
            {
                "id": "stage-03-routing-owner-gate",
                "owner_routes": [
                    {"burden_id": "B1", "owner_id": "do-second-loop"},
                    {"burden_id": "B2", "owner_id": "P3-reason-revelation-tension"},
                ],
            }
        ]
    )
    for required in (
        "DO_SECOND_LOOP operations: accountability-hujjah-compression",
        "DO_SECOND_LOOP is a delta/register vocabulary family for callable owner `do-second-loop`",
        "coercive-guidance-demand",
        "punishment-proportionality-accountability",
        "DO_SECOND_LOOP: accountability-hujjah-narrowed",
        "coercive-guidance-demand-bounded",
        "punishment-proportionality-calibrated",
        "P3 operations: order, reason-revelation-tension",
        "P3: reason-revelation-order-stabilized",
    ):
        if required not in do_second_loop_guidance:
            raise HarnessError(f"Self-test Stage 04 do-second-loop/P3 guidance omitted {required}")
    v2_pattern_rows = [
        "⟦ACT ¹B₁[V2.reconstituting-reason] :: π=reason-as-sovereign-tribunal :: body_ref=¹B₁ :: Δ=Δ¹B:reason-role-repaired :: Land(¹B)+⟧",
        "⟦ACT ²B₁[pattern-profiling.loaded-label-carrier-audit] :: π=worldview-carrier-compression :: body_ref=²B₁ :: Δ=Δ²B:carrier-function-typed :: Land(²B)+⟧",
    ]
    normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1", "B2"],
            "act_burdens": ["B1", "B2"],
            "act_rows": v2_pattern_rows,
            "act_row_details": self_test_act_row_details(
                v2_pattern_rows,
                {
                    "¹B₁": "ξ",
                    "²B₁": "μ",
                },
            ),
        },
    )
    v2_reason_axis_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [v2_pattern_rows[0]],
            "act_row_details": self_test_act_row_details(
                [v2_pattern_rows[0]],
                {
                    "¹B₁": "m",
                },
            ),
        },
    )
    if v2_reason_axis_stage04["act_row_details"][0].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to canonicalize V2 reconstituting-reason register_axis fallback")
    v2_reason_role_row = (
        "⟦ACT ¹B₁[V2.reason-role-repair] :: π=reason-revelation-rank-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:reason-role-repaired :: Land(¹B)+⟧"
    )
    v2_reason_role_axis_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [v2_reason_role_row],
            "act_row_details": self_test_act_row_details(
                [v2_reason_role_row],
                {
                    "¹B₁": "σ",
                },
            ),
        },
    )
    if v2_reason_role_axis_stage04["act_row_details"][0].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to canonicalize V2 reason-role-repair register_axis fallback")
    v2_proof_burden_order_row = (
        "⟦ACT ¹B₁[V2.proof-burden-order] :: π=moral-theological-burden-order :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:burden-order-repaired :: Land(¹B)+⟧"
    )
    v2_proof_burden_axis_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [v2_proof_burden_order_row],
            "act_row_details": self_test_act_row_details(
                [v2_proof_burden_order_row],
                {
                    "¹B₁": "τ",
                },
            ),
        },
    )
    if v2_proof_burden_axis_stage04["act_row_details"][0].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to canonicalize V2 proof-burden-order register_axis fallback")
    v2_proof_burden_h_axis_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [v2_proof_burden_order_row],
            "act_row_details": self_test_act_row_details(
                [v2_proof_burden_order_row],
                {
                    "¹B₁": "H",
                },
            ),
        },
    )
    if v2_proof_burden_h_axis_stage04["act_row_details"][0].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to canonicalize V2 proof-burden-order H-axis fallback")
    if (
        v2_proof_burden_axis_stage04["act_row_details"][0].get("delta_result")
        != "proof-burden-order-restored"
    ):
        raise HarnessError("Self-test failed to canonicalize V2 proof-burden-order delta_result fallback")
    selected_model_controlled_rows = [
        "⟦ACT ¹B₁[do-christian-extensions.model-identification] :: π=selected-model-person-nature-transfer :: body_ref=¹B₁ :: Δ=Δ¹B:trinitarian-model-identified :: Land(¹B)+⟧",
        "⟦ACT ¹B₂[M9.predication-repair] :: π=selected-only-true-god-predicate-transfer :: body_ref=¹B₂ :: Δ=Δ¹B:person-nature-transfer-blocked :: Land(¹B)+⟧",
        "⟦ACT ²B₁[M7.definition-anchor] :: π=only-placement-analogy :: body_ref=²B₁ :: Δ=Δ²B:definition-anchored :: Land(²B)+⟧",
        "⟦ACT ²B₂[M9.predication-repair] :: π=2-plus-2-predicate-category :: body_ref=²B₂ :: Δ=Δ²B:category-separated :: Land(²B)+⟧",
        "⟦ACT ³B₁[source-status-repair.source-order] :: π=selected-proof-stack :: body_ref=³B₁ :: Δ=Δ³B:proof-text-sorted :: Land(³B)+⟧",
        "⟦ACT ³B₂[authority-order-repair.sort] :: π=proof-text-hidden-support :: body_ref=³B₂ :: Δ=Δ³B:proof-text-hidden-support-blocked :: Land(³B)+⟧",
        "⟦ACT ⁴B₁[M8.consequence-trace] :: π=selected-entailment-pressure :: body_ref=⁴B₁ :: Δ=Δ⁴B:entailment-blocked :: Land(⁴B)+⟧",
        "⟦ACT ⁴B₂[M9.predication-repair] :: π=sender-sent-relation-category :: body_ref=⁴B₂ :: Δ=Δ⁴B:referent-separated :: Land(⁴B)+⟧",
    ]
    normalized_selected_model_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1", "B2", "B3", "B4"],
            "act_burdens": ["B1", "B2", "B3", "B4"],
            "act_rows": selected_model_controlled_rows,
            "act_row_details": self_test_act_row_details(
                selected_model_controlled_rows,
                {
                    "¹B₁": "Ω",
                    "¹B₂": "Ω",
                    "²B₁": "μ",
                    "²B₂": "μ",
                    "³B₁": "σ",
                    "³B₂": "σ",
                    "⁴B₁": "κ",
                    "⁴B₂": "Ω",
                },
            ),
        },
    )
    selected_model_delta_results = [
        stage04_act_details_by_ref(normalized_selected_model_stage04)[ref]["delta_result"]
        for ref in ["¹B₁", "¹B₂", "²B₁", "²B₂", "³B₁", "³B₂", "⁴B₁", "⁴B₂"]
    ]
    if selected_model_delta_results != [
        "trinitarian-model-identified",
        "person-nature-transfer-blocked",
        "definition-anchored",
        "category-separated",
        "proof-text-sorted",
        "proof-text-hidden-support-blocked",
        "entailment-blocked",
        "referent-separated",
    ]:
        raise HarnessError("Self-test failed to preserve exact controlled Stage 04 delta_result tokens")
    rewrites = normalized_selected_model_stage04.get("normalization", {}).get("delta_result_canonicalizations")
    if rewrites:
        raise HarnessError("Self-test laundered selected DO-family Stage 04 delta_result tokens")
    m8_dependency_row = (
        "⟦ACT ¹B₁[M8.dependency-trace] :: "
        "π=dependency-carrier-pressure :: "
        "body_ref=¹B₁ :: Δ=Δκ:dependency-exposed :: Land(¹B)+⟧"
    )
    normalized_m8_dependency_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [m8_dependency_row],
            "act_row_details": self_test_act_row_details(
                [m8_dependency_row],
                {"¹B₁": "κ"},
            ),
        },
    )
    if stage04_act_details_by_ref(normalized_m8_dependency_stage04)["¹B₁"]["delta_result"] != "dependency-exposed":
        raise HarnessError("Self-test failed to preserve M8 dependency-trace dependency-exposed delta")
    invalid_m8_dependency_row = (
        "⟦ACT ¹B₁[M8.dependency-trace] :: "
        "π=dependency-carrier-pressure :: "
        "body_ref=¹B₁ :: Δ=Δκ:entailment-blocked :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_m8_dependency_row],
                "act_row_details": self_test_act_row_details(
                    [invalid_m8_dependency_row],
                    {"¹B₁": "κ"},
                ),
            },
        )
    except HarnessError as exc:
        if "M8.dependency-trace requires operation-specific delta_result 'dependency-exposed'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted M8 dependency-trace with entailment-blocked delta")
    invalid_m9_operation_row = (
        "⟦ACT ¹B₁[M9.category-or-referent-separation] :: "
        "π=predicate-category-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:category-separated :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_m9_operation_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled operation vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted M9 delta/result label as an operation token")
    invalid_delta_row = (
        "⟦ACT ¹B₁[do-christian-extensions.model-identification] :: "
        "π=selected-model-person-nature-transfer :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:selected-model-transfer-bounded :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_delta_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted near-synonym Stage 04 delta_result laundering")
    borrowed_do_attribute_delta_row = (
        "⟦ACT ¹B₁[M9.predication-repair] :: "
        "π=predicate-identity-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:predicate-identity-separated :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [borrowed_do_attribute_delta_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted DO_ATTRIBUTE delta_result borrowed by M9")
    proof_method_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-family-and-carrier-audit] :: "
        "π=proof-family-carrier-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-family-carrier-typed :: Land(¹B)+⟧"
    )
    normalized_proof_method_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_method_row],
            "act_row_details": self_test_act_row_details([proof_method_row], {"¹B₁": "ξ"}),
        },
    )
    proof_method_detail = stage04_act_details_by_ref(normalized_proof_method_stage04)["¹B₁"]
    if proof_method_detail.get("owner") != "proof-method-audit":
        raise HarnessError("Self-test failed to preserve proof-method-audit ACT owner")
    if proof_method_detail.get("delta_result") != "proof-family-carrier-typed":
        raise HarnessError("Self-test failed to preserve proof-method-audit delta_result")
    proof_method_tau_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_method_row],
            "act_row_details": self_test_act_row_details([proof_method_row], {"¹B₁": "τ"}),
        },
    )
    if proof_method_tau_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to accept proof-method tribunal/burden-function register_axis")
    proof_overreach_tau_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-overreach-audit] :: "
        "π=formalization-validity :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-overreach-bounded :: Land(¹B)+⟧"
    )
    proof_overreach_tau_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_overreach_tau_row],
            "act_row_details": self_test_act_row_details([proof_overreach_tau_row], {"¹B₁": "τ"}),
        },
    )
    if proof_overreach_tau_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to accept proof-overreach tribunal/burden-function register_axis")
    proof_overreach_h_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_overreach_tau_row],
            "act_row_details": self_test_act_row_details([proof_overreach_tau_row], {"¹B₁": "H"}),
        },
    )
    if proof_overreach_h_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to canonicalize proof-overreach H fallback to tribunal axis")
    proof_overreach_m_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_overreach_tau_row],
            "act_row_details": self_test_act_row_details([proof_overreach_tau_row], {"¹B₁": "m"}),
        },
    )
    if proof_overreach_m_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to canonicalize proof-overreach m fallback to tribunal axis")
    invalid_proof_method_operation_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-stack-routed] :: "
        "π=proof-family-carrier-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-family-carrier-typed :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_proof_method_operation_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled operation vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted proof-method route label as operation token")
    proof_route_status_tau_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-route-status-audit] :: "
        "π=proof-route-status :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-route-status-clarified :: Land(¹B)+⟧"
    )
    proof_route_status_tau_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_route_status_tau_row],
            "act_row_details": self_test_act_row_details([proof_route_status_tau_row], {"¹B₁": "τ"}),
        },
    )
    if proof_route_status_tau_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to accept proof-route-status tribunal/burden-function register_axis")
    proof_route_status_h_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_route_status_tau_row],
            "act_row_details": self_test_act_row_details([proof_route_status_tau_row], {"¹B₁": "H"}),
        },
    )
    if proof_route_status_h_stage04["act_row_details"][0].get("register_axis") != "τ":
        raise HarnessError("Self-test failed to canonicalize proof-route-status H fallback to tribunal axis")
    invalid_proof_method_tau_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-family-classification] :: "
        "π=proof-family-label :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-family-carrier-typed :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_proof_method_tau_row],
                "act_row_details": self_test_act_row_details([invalid_proof_method_tau_row], {"¹B₁": "τ"}),
            },
        )
    except HarnessError as exc:
        if "register_axis 'τ' is not approved for owner proof-method-audit.proof-family-classification" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted generic proof-method tau register_axis")
    valid_proof_family_classification_pressure_row = (
        "⟦ACT ¹B₁[proof-method-audit.proof-family-classification] :: "
        "π=proof-family-classification-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-family-carrier-typed :: Land(¹B)+⟧"
    )
    normalized_proof_family_classification_pressure_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [valid_proof_family_classification_pressure_row],
            "act_row_details": self_test_act_row_details(
                [valid_proof_family_classification_pressure_row],
                {"¹B₁": "τ"},
            ),
        },
    )
    valid_proof_family_classification_pressure_detail = stage04_act_details_by_ref(
        normalized_proof_family_classification_pressure_stage04
    )["¹B₁"]
    valid_proof_family_classification_pressure_typed_detail = (
        normalized_proof_family_classification_pressure_stage04["act_row_details"][0]
    )
    if valid_proof_family_classification_pressure_detail.get("operation") != "proof-family-and-carrier-audit":
        raise HarnessError(
            "Self-test failed to canonicalize proof-family-classification-pressure "
            "to proof-family-and-carrier-audit"
        )
    if valid_proof_family_classification_pressure_typed_detail.get("register_axis") != "τ":
        raise HarnessError(
            "Self-test failed to preserve tribunal/burden-function register_axis for "
            "proof-family-classification-pressure"
        )
    valid_do_attribute_delta_row = (
        "⟦ACT ¹B₁[do-attribute-precision.attribute-precision] :: "
        "π=predicate-identity-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:predicate-identity-separated :: Land(¹B)+⟧"
    )
    normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [valid_do_attribute_delta_row],
            "act_row_details": self_test_act_row_details([valid_do_attribute_delta_row], {"¹B₁": "Ω"}),
        },
    )
    invalid_do_attribute_family_owner_row = (
        "⟦ACT ¹B₁[DO_ATTRIBUTE.attribute-precision] :: "
        "π=predicate-identity-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:predicate-identity-separated :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_do_attribute_family_owner_row],
            },
        )
    except HarnessError as exc:
        if "delta/register family alias" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted DO_ATTRIBUTE family alias as executable ACT owner")
    m9_residue_row = (
        "⟦ACT ¹B₁[M9.predication-repair] :: "
        "π=residue-slippage-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:sense-separated :: Land(¹B)+⟧"
    )
    accepted_m9_residue_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [m9_residue_row],
            "act_row_details": self_test_act_row_details([m9_residue_row], {"¹B₁": "xi"}),
        },
    )
    if accepted_m9_residue_stage04["act_row_details"][0].get("register_axis") != "ξ":
        raise HarnessError("Self-test failed to accept M9 residue/slippage register_axis")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [m9_residue_row],
                "act_row_details": self_test_act_row_details([m9_residue_row], {"¹B₁": "σ"}),
            },
        )
    except HarnessError as exc:
        if "register_axis 'σ' is not approved for owner M9" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted source-status register_axis for M9")
    invalid_m9_delta_as_operation_row = (
        "⟦ACT ¹B₁[M9.referent-separated] :: "
        "π=referent-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:referent-separated :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_m9_delta_as_operation_row],
                "act_row_details": self_test_act_row_details(
                    [invalid_m9_delta_as_operation_row],
                    {"¹B₁": "μ"},
                ),
            },
        )
    except HarnessError as exc:
        if "operation token 'referent-separated' is outside controlled operation vocabulary for M9" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted M9 delta_result token as callable operation")
    source_stack_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=quran-hadith-lexical-source-stack :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-text-sorted :: Land(¹B)+⟧"
    )
    source_recoil_row = (
        "⟦ACT ¹B₂[source-status-repair.source-order] :: "
        "π=source-order-recoil-hidden-support :: "
        "body_ref=¹B₂ :: Δ=Δ¹B:hidden-support-blocked :: Land(¹B)+⟧"
    )
    normalized_source_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [source_stack_row, source_recoil_row],
            "act_row_details": self_test_act_row_details(
                [source_stack_row, source_recoil_row],
                {"¹B₁": "σ", "¹B₂": "σ"},
            ),
        },
    )
    source_delta_results = [
        stage04_act_details_by_ref(normalized_source_stage04)[ref]["delta_result"]
        for ref in ["¹B₁", "¹B₂"]
    ]
    if source_delta_results != ["proof-text-sorted", "hidden-support-blocked"]:
        raise HarnessError("Self-test failed to preserve exact SOURCE delta_result tokens")
    proof_text_recoil_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order-repair] :: "
        "π=proof-text-source-order-recoil :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:source-order-repaired :: Land(¹B)+⟧"
    )
    proof_text_recoil_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [proof_text_recoil_row],
            "act_row_details": self_test_act_row_details(
                [proof_text_recoil_row],
                {"¹B₁": "σ"},
            ),
        },
    )
    proof_text_recoil_details = stage04_act_details_by_ref(proof_text_recoil_stage04)
    if proof_text_recoil_details["¹B₁"]["delta_result"] != "proof-text-hidden-support-blocked":
        raise HarnessError("Self-test failed to canonicalize SOURCE proof-text recoil delta")
    invalid_source_hidden_support_delta_row = (
        "⟦ACT ¹B₃[authority-order-repair.sort] :: "
        "π=hidden-support-and-source-function-pressure :: "
        "body_ref=¹B₃ :: Δ=Δ¹B:authority-order-separated :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_hidden_support_delta_row],
                "act_row_details": self_test_act_row_details(
                    [invalid_source_hidden_support_delta_row],
                    {"¹B₃": "σ"},
                ),
            },
        )
    except HarnessError as exc:
        if "hidden-support pressure must use delta_result token 'hidden-support-blocked'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted SOURCE hidden-support pressure with authority-order delta")
    invalid_source_operation_row = (
        "⟦ACT ¹B₁[source-status-repair.hidden-support-block] :: "
        "π=source-order-recoil-hidden-support :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:proof-text-hidden-support-blocked :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_operation_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled operation vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted source-status result pressure as operation token")
    invalid_source_status_operation_row = (
        "⟦ACT ¹B₁[source-status-repair.status] :: "
        "π=source-status-label-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:source-function-bounded :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_status_operation_row],
                "act_row_details": self_test_act_row_details(
                    [invalid_source_status_operation_row],
                    {"¹B₁": "σ"},
                ),
            },
        )
    except HarnessError as exc:
        if "outside controlled operation vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted SOURCE status label as callable operation")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [source_stack_row],
                "act_row_details": self_test_act_row_details([source_stack_row], {"¹B₁": "μ"}),
            },
        )
    except HarnessError as exc:
        if "register_axis 'μ' is not approved for owner source-status-repair" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted memetic-carrier register_axis for source-status repair")
    invalid_source_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=quran-hadith-lexical-source-stack :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:source-order-repaired-via-prose :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted prose-derived SOURCE delta_result laundering")
    source_family_authority_row = (
        "⟦ACT ¹B₁[SOURCE.authority-order-repair] :: "
        "π=authority-rank-tribunal-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:authority-order-repaired :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [source_family_authority_row],
                "act_row_details": self_test_act_row_details([source_family_authority_row], {"¹B₁": "σ"}),
            },
        )
    except HarnessError as exc:
        if "SOURCE" not in str(exc) or "delta/register family alias" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted SOURCE family alias as executable ACT owner")
    source_callable_authority_row = (
        "⟦ACT ¹B₁[authority-order-repair.authority-order-repair] :: "
        "π=authority-rank-tribunal-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:authority-order-repaired :: Land(¹B)+⟧"
    )
    normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [source_callable_authority_row],
            "act_row_details": self_test_act_row_details([source_callable_authority_row], {"¹B₁": "σ"}),
        },
    )
    invalid_source_formal_source_pair_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=source-lineage-quotation-order :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:source-order-repaired :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_formal_source_pair_row],
            },
        )
    except HarnessError as exc:
        if "requires operation 'source-order-repair'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted source-order-repaired without source-order-repair operation")
    invalid_source_formal_authority_pair_row = (
        "⟦ACT ¹B₁[authority-order-repair.source-order] :: "
        "π=authority-rank-tribunal-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:authority-order-repaired :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_source_formal_authority_pair_row],
            },
        )
    except HarnessError as exc:
        if "requires operation 'authority-order-repair'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted authority-order-repaired without authority-order-repair operation")
    do_second_loop_rows = [
        "⟦ACT ¹B₁[do-second-loop.accountability-hujjah-compression] :: π=accountability-hujjah-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:accountability-hujjah-narrowed :: Land(¹B)+⟧",
        "⟦ACT ¹B₂[do-second-loop.coercive-guidance-demand] :: π=coercive-guidance-demand :: body_ref=¹B₂ :: Δ=Δ¹B:coercive-guidance-demand-bounded :: Land(¹B)+⟧",
        "⟦ACT ¹B₃[do-second-loop.punishment-proportionality-accountability] :: π=punishment-proportionality-pressure :: body_ref=¹B₃ :: Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧",
    ]
    normalized_do_second_loop_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": do_second_loop_rows,
            "act_row_details": self_test_act_row_details(
                do_second_loop_rows,
                {"¹B₁": "κ", "¹B₂": "Ω", "¹B₃": "♥"},
            ),
        },
    )
    do_second_loop_delta_results = [
        stage04_act_details_by_ref(normalized_do_second_loop_stage04)[ref]["delta_result"]
        for ref in ["¹B₁", "¹B₂", "¹B₃"]
    ]
    if do_second_loop_delta_results != [
        "accountability-hujjah-narrowed",
        "coercive-guidance-demand-bounded",
        "punishment-proportionality-calibrated",
    ]:
        raise HarnessError("Self-test failed to preserve exact DO_SECOND_LOOP delta_result tokens")
    invalid_do_second_loop_family_owner_row = (
        "⟦ACT ¹B₁[DO_SECOND_LOOP.accountability-hujjah-compression] :: "
        "π=accountability-hujjah-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:accountability-hujjah-narrowed :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_do_second_loop_family_owner_row],
            },
        )
    except HarnessError as exc:
        if "delta/register family alias" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted DO_SECOND_LOOP family alias as executable ACT owner")
    invalid_do_second_loop_delta_row = (
        "⟦ACT ¹B₁[do-second-loop.accountability-hujjah-compression] :: "
        "π=accountability-hujjah-pressure :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:scope-boundary-named :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [invalid_do_second_loop_delta_row],
            },
        )
    except HarnessError as exc:
        if "outside controlled vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted P7 delta_result borrowed by do-second-loop")
    p3_long_owner_row = (
        "⟦ACT ¹B₁[P3-reason-revelation-tension.reason-revelation-tension] :: "
        "π=reason-revelation-public-admissibility-order :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:reason-revelation-order-stabilized :: Land(¹B)+⟧"
    )
    normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [p3_long_owner_row],
            "act_row_details": self_test_act_row_details([p3_long_owner_row], {"¹B₁": "Ω"}),
        },
    )
    p3_abbreviated_owner_row = (
        "⟦ACT ¹B₁[P3.reason-revelation-tension] :: "
        "π=reason-revelation-public-admissibility-order :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:reason-revelation-order-stabilized :: Land(¹B)+⟧"
    )
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [p3_abbreviated_owner_row],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner_id": "P3-reason-revelation-tension",
                        "operation": "reason-revelation-tension",
                        "register_axis": "Ω",
                        "delta_result": "reason-revelation-order-stabilized",
                        "act_row": p3_abbreviated_owner_row,
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "owner_id disagrees with parsed ACT row" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted abbreviated P3 owner token for long-owner ACT row")
    partition_stage04 = dict(normalized_stage04)
    partition_stage04["act_body_refs"] = ["¹B₁", "¹B₂", "²B₁", "²B₂", "³B₁", "³B₂", "⁴B₁", "⁴B₂", "⁵B₁", "⁵B₂"]
    partition_plan = compiled_release_section_plan(70)
    plan_roles = [role for _section_id, role in partition_plan]
    if plan_roles.index("field_witness_nar") <= plan_roles.index("closing_formulation"):
        raise HarnessError("Self-test compiled section plan must place field_witness after Closing Formulation")
    partition = compiled_act_partition([partition_stage04], partition_plan)
    budgets = compiled_section_budgets(partition_plan, 70)
    if not isinstance(budgets, dict) or budgets.get("schema") != staged_output.SECTION_BUDGET_SCHEMA:
        raise HarnessError("Self-test failed to derive compiled section budgets")
    if budgets.get("target_output_bytes") != 70 * 1024:
        raise HarnessError("Self-test compiled section budgets used the wrong target byte floor")
    min_section_bytes = budgets.get("min_section_bytes")
    if not isinstance(min_section_bytes, dict):
        raise HarnessError("Self-test compiled section budgets did not produce per-section floors")
    planned_section_ids = {section_id for section_id, _role in partition_plan}
    if set(min_section_bytes) != planned_section_ids:
        raise HarnessError("Self-test compiled section budgets did not cover every section exactly once")
    if any(not isinstance(value, int) or value <= 0 for value in min_section_bytes.values()):
        raise HarnessError("Self-test compiled section budgets produced a non-positive section floor")
    if sum(min_section_bytes.values()) != 70 * 1024:
        raise HarnessError("Self-test compiled section budgets did not distribute the full target floor")
    try:
        validate_compiled_budget_preflight("compiled-output", 70, 0)
    except HarnessError as exc:
        if "--section-expansion-rounds >= 1" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject budgeted compiled output without expansion capacity")
    validate_compiled_budget_preflight("compiled-output", 70, 1)
    validate_compiled_budget_preflight("single-output", 70, 0)
    invalid_assembly_manifest = staged_output.manifest_for_sections(
        run_dir / "invalid-assembly-wrapper",
        case_id="self-test-compiled-assembly-error-wrapper",
        source_input="self-test",
        section_specs=staged_output.small_sections(),
        section_budgets={
            "schema": staged_output.SECTION_BUDGET_SCHEMA,
            "target_output_bytes": 0,
            "role_min_bytes": {},
            "min_section_bytes": {"opening": 100000},
        },
    )
    try:
        assemble_compiled_manifest(invalid_assembly_manifest, root=root)
    except HarnessError as exc:
        if "stage-07-release-output: assembly failed:" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to wrap compiled assembly errors as HarnessError")
    graph_line, graph_roots, graph_parallel = stage07_dependency_graph_scaffold(["B1", "B2", "B3"], [])
    if graph_line != "B1 (root) || B2 (root) || B3 (root)":
        raise HarnessError("Self-test Stage 07 graph scaffold omitted edge-empty parallel roots")
    if graph_roots != ["B1", "B2", "B3"] or graph_parallel != [["B1", "B2", "B3"]]:
        raise HarnessError("Self-test Stage 07 graph scaffold did not mirror edge-empty roots/parallel group")
    edgeful_graph_line, edgeful_roots, edgeful_parallel = stage07_dependency_graph_scaffold(
        ["B1", "B2", "B3", "B4", "B5"],
        [{"from": "B4", "to": "B5", "type": "generated_burden_instantiation"}],
    )
    for required_graph_token in ("B1 (root)", "B2 (root)", "B3 (root)", "B4 (root)", "B4 -> B5"):
        if required_graph_token not in edgeful_graph_line:
            raise HarnessError(f"Self-test Stage 07 edgeful graph scaffold omitted {required_graph_token}")
    if edgeful_roots != ["B1", "B2", "B3", "B4"] or edgeful_parallel:
        raise HarnessError("Self-test Stage 07 edgeful graph scaffold did not derive roots from incoming edges")
    assigned_once = [
        ref
        for assignment in partition["assignments"]
        for ref in assignment["body_refs"]
    ]
    if sorted(assigned_once) != sorted(partition_stage04["act_body_refs"]):
        raise HarnessError("Self-test failed to assign every Stage 04 ACT body_ref exactly once")
    if len(assigned_once) != len(set(assigned_once)):
        raise HarnessError("Self-test produced duplicate compiled ACT partition assignments")
    if any(not assignment["body_refs"] for assignment in partition["assignments"]):
        raise HarnessError("Self-test compiled ACT partition left an ACT section empty for this fixture")
    expected_partition = [
        ["¹B₁", "¹B₂", "²B₁", "²B₂"],
        ["³B₁", "³B₂"],
        ["⁴B₁", "⁴B₂", "⁵B₁", "⁵B₂"],
    ]
    actual_partition = [assignment["body_refs"] for assignment in partition["assignments"]]
    if actual_partition != expected_partition:
        raise HarnessError(f"Self-test compiled ACT partition did not preserve whole burden groups: {actual_partition}")
    small_partition = partition_body_refs(["¹B₁", "¹B₂", "²B₁", "²B₂"], [assignment["section_id"] for assignment in partition["assignments"]])
    if [ref for assignment in small_partition for ref in assignment["body_refs"]] != ["¹B₁", "¹B₂", "²B₁", "²B₂"]:
        raise HarnessError("Self-test small ACT partition did not preserve input body_ref order")
    normalized_stage04_rich_burdens = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["¹B / B1 source-order diagnostic burden"],
            "act_rows": [canonical_act_row],
            "act_row_details": self_test_act_row_details([canonical_act_row], {"¹B₁": "σ"}),
        },
    )
    if normalized_stage04_rich_burdens.get("act_burdens") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 04 act_burdens into burden ids")
    if not isinstance(normalized_stage04_rich_burdens.get("act_burdens_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 04 act_burdens details")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["source-order diagnostic burden without canonical id"],
                "act_rows": [canonical_act_row],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 04 act_burdens without canonical id")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [{"burden_id": "B1", "body_ref": "¹B₁"}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 04 object-shaped act_rows without act_row")
    stage_local_record = base_record(
        "self-test-a9-science-source-stage03",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-03-routing-owner-gate",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage03",
            replay_record,
            stop_after_stage="stage-03-routing-owner-gate",
        ),
    )
    stage_local_record["stages"] = [*replay["stages"][:2], normalized]
    stage_local_path = run_dir / "staged-handoff-stage03-model-scope-record.json"
    write_json(stage_local_path, stage_local_record)
    validate_replay_record(root, stage_local_path)

    stage04_local_record = base_record(
        "self-test-a9-science-source-stage04",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-04-burden-execution-act",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage04",
            replay_record,
            stop_after_stage="stage-04-burden-execution-act",
        ),
    )
    stage04_local_record["stages"] = [*replay["stages"][:3], normalized_stage04]
    stage04_local_path = run_dir / "staged-handoff-stage04-model-scope-record.json"
    write_json(stage04_local_path, stage04_local_record)
    validate_replay_record(root, stage04_local_path)

    normalized_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "Stage 04 ACT burden B1 landed; reread produced no generated burden.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [self_test_reread_entry("B1")],
            "terminal_state_details": [
                {
                    "burden_id": "B1",
                    "terminal_state": "landed",
                    "basis": [
                        "Live-style detail row; normalizer must preserve controlled terminal state.",
                        "List basis preserves multiple evidence clauses without becoming a delta_result.",
                    ],
                }
            ],
        },
    )
    terminal_detail = normalized_stage05.get("terminal_state_details", [{}])[0]
    if terminal_detail.get("state") != "landed":
        raise HarnessError("Self-test failed to normalize Stage 05 terminal_state detail into state")
    terminal_basis = terminal_detail.get("basis")
    if not isinstance(terminal_basis, list) or len(terminal_basis) != 2:
        raise HarnessError("Self-test failed to preserve Stage 05 terminal_state detail list basis")
    complex_delta_reread_entry = self_test_reread_entry(
        "B1",
        reread=(
            "R(H,ΔB1:source-order-repaired+ΔB1:source-function-bounded) "
            "held routes rechecked: none; live remainder: no source burden remains; "
            "release/next: STOP."
        ),
    )
    complex_delta_reread_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after the terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [complex_delta_reread_entry],
        },
    )
    if not str(complex_delta_reread_stage05["per_burden_reread"][0].get("reread") or "").startswith("R(H,Δ):"):
        raise HarnessError("Self-test failed to canonicalize complex burden-delta R(H,Δ...) reread invocation")
    two_burden_act_rows = [
        canonical_act_row,
        (
            "⟦ACT ²B₁[M8.consequence-trace] :: "
            "π=next-burden-pressure :: body_ref=²B₁ :: "
            "Δ=Δ²B:consequence-traced :: Land(²B)+⟧"
        ),
    ]
    two_burden_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1", "B2"],
            "act_burdens": ["B1", "B2"],
            "act_rows": two_burden_act_rows,
            "act_row_details": self_test_act_row_details(
                two_burden_act_rows,
                {"¹B₁": "σ", "²B₁": "κ"},
            ),
        },
    )
    b2_stop_entry_with_nested_proof = self_test_reread_entry(
        "B2",
        reread=(
            "R(H,Δ²B): held routes rechecked: none; live remainder: "
            "no remaining burden; release/next: STOP after ²B."
        ),
    )
    b2_stop_entry_with_nested_proof["no_new_resultant_proof"] = {
        "escape_routes_checked": ["self-test route"],
        "proved": True,
    }
    two_stop_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed", "B2": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after either terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [
                self_test_reread_entry("B1"),
                b2_stop_entry_with_nested_proof,
            ],
        },
    )
    top_level_pressure_entry = self_test_reread_entry("B1")
    expected_pressure_activations = copy.deepcopy(top_level_pressure_entry["pressure_activations"])
    top_level_pressure_entry.pop("pressure_activations")
    top_level_pressure_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after the terminal read.",
                "unresolved_burdens": [],
            },
            "pressure_activations": expected_pressure_activations,
            "per_burden_reread": [top_level_pressure_entry],
        },
    )
    hydrated_pressure = top_level_pressure_stage05["per_burden_reread"][0].get("pressure_activations")
    if hydrated_pressure != expected_pressure_activations:
        raise HarnessError("Self-test failed to hydrate per-burden pressure slots from Stage 05 top-level object")
    pressure_normalization = top_level_pressure_stage05.get("normalization", {})
    if pressure_normalization.get("per_burden_pressure_activations_from_stage_level") != ["B1"]:
        raise HarnessError("Self-test Stage 05 pressure-slot hydration did not record normalization")
    non_edge_pressure_entry = self_test_reread_entry("B1")
    non_edge_pressure_entry["pressure_activations"]["dependency-tug"] = (
        "dependency-tug: P7.scope-boundary pressure class: dependency-tug -- "
        "remaining dependency pressure is bounded and does not license a B1 -> B2 edge."
    )
    non_edge_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after the terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [non_edge_pressure_entry],
        },
    )
    sanitized_non_edge = non_edge_stage05["per_burden_reread"][0]["pressure_activations"]["dependency-tug"]
    if "B2" in sanitized_non_edge or "-> B2" in sanitized_non_edge:
        raise HarnessError("Self-test Stage 05 negative non-edge public burden reference was not sanitized")
    non_edge_events = (
        non_edge_stage05.get("normalization") or {}
    ).get("negative_non_edge_public_burden_references")
    if not isinstance(non_edge_events, list) or not non_edge_events:
        raise HarnessError("Self-test Stage 05 negative non-edge sanitation did not record normalization")
    validate_incremental_handoffs([two_burden_stage04, two_stop_stage05])
    continuation_entries = {
        str(entry["burden_id"]): entry
        for entry in two_stop_stage05["per_burden_reread"]
    }
    b1_continuation = continuation_entries["B1"]
    if b1_continuation.get("route_result_type") != "held_burden_activation":
        raise HarnessError("Self-test failed to normalize intermediate B1 STOP into held_burden_activation")
    if b1_continuation.get("route") != "RECURSE" or b1_continuation.get("graph_delta") != "B1 -> B2":
        raise HarnessError("Self-test failed to normalize intermediate B1 route/graph continuation")
    if b1_continuation.get("matched_route") != "Matched owner/TTP route: [M8.consequence-trace]":
        raise HarnessError("Self-test failed to project B2 matched owner route onto intermediate B1 MRP")
    rendered_continuation = staged_output.render_mrp_block(b1_continuation)
    if "Matched owner/TTP route: [M8.consequence-trace]" not in rendered_continuation:
        raise HarnessError("Self-test failed to render matched owner route in normalized MRP block")
    held_with_reason_target_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after either terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [
                self_test_reread_entry("B1"),
                self_test_reread_entry("B2"),
            ],
        },
    )
    validate_incremental_handoffs([two_burden_stage04, held_with_reason_target_stage05])
    held_with_reason_entries = {
        str(entry["burden_id"]): entry
        for entry in held_with_reason_target_stage05["per_burden_reread"]
    }
    if held_with_reason_entries["B1"].get("route_result_type") != "held_burden_activation":
        raise HarnessError("Self-test failed to normalize intermediate STOP before held-with-reason burden")
    two_held_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed", "B2": "landed"},
            "dependency_graph_edges": [
                {"from": "B1", "to": "B2", "type": "held_burden_activation"}
            ],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after either terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [
                self_test_reread_entry("B1", next_burden_id="B2"),
                self_test_reread_entry("B2"),
            ],
        },
    )
    validate_incremental_handoffs([two_burden_stage04, two_held_stage05])
    held_entries = {
        str(entry["burden_id"]): entry
        for entry in two_held_stage05["per_burden_reread"]
    }
    if held_entries["B1"].get("matched_route") != "Matched owner/TTP route: [M8.consequence-trace]":
        raise HarnessError("Self-test failed to hydrate matched route for already-held MRP activation")
    if not ((two_held_stage05.get("normalization") or {}).get("matched_route_hydrations")):
        raise HarnessError("Self-test failed to record already-held matched route hydration metadata")
    if not any(
        stage05_edge_endpoints(edge) == ("B1", "B2", "held_burden_activation")
        for edge in two_stop_stage05.get("dependency_graph_edges", [])
    ):
        raise HarnessError("Self-test failed to record held_burden_activation edge for intermediate STOP")
    string_edges = stage05_dependency_edges(
        {"dependency_graph_edges": ["B1 -> B2", "¹B → ²B"]}
    )
    if not any(edge == {"from": "B1", "to": "B2", "type": "held_burden_activation"} for edge in string_edges):
        raise HarnessError("Self-test failed to parse Stage 05 string dependency graph edge")
    held_gradient_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed", "B2": "landed"},
            "dependency_graph_edges": ["B1 -> B2"],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "No generated MRP burden emerged after either terminal read.",
                "unresolved_burdens": [],
            },
            "per_burden_reread": [
                self_test_reread_entry(
                    "B1",
                    next_burden_id="B2",
                    route_gradient="plain-gradient keeps route pressure after R(H,Δ)",
                ),
                self_test_reread_entry("B2"),
            ],
        },
    )
    held_gradient = str(held_gradient_stage05["per_burden_reread"][0].get("route_gradient") or "")
    if "already-held B2 from B_LA" not in held_gradient:
        raise HarnessError("Self-test failed to add held-route machine identity to visible Stage 05 gradient")
    if not ((held_gradient_stage05.get("normalization") or {}).get("held_route_gradient_identity")):
        raise HarnessError("Self-test failed to record Stage 05 held route-gradient identity normalization")
    if "no_new_resultant_proof" in continuation_entries["B2"]:
        raise HarnessError("Self-test failed to strip wrongly nested per-burden no_new_resultant_proof")
    if not str(continuation_entries["B2"].get("reread") or "").startswith("R(H,Δ):"):
        raise HarnessError("Self-test failed to canonicalize burden-specific R(H,Δn) reread invocation")
    try:
        normalized_stage(
            "stage-05-mrp-reread-terminal-state",
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "terminal_states": {"B1": "landed"},
                "dependency_graph_edges": [],
                "no_new_resultant_proof": True,
                "terminal_state_details": [
                    {"burden_id": "B1", "state": "held", "terminal_state": "landed"}
                ],
            },
        )
    except HarnessError as exc:
        if "state and .terminal_state must match" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted conflicting Stage 05 terminal state detail dialect")
    try:
        normalized_stage(
            "stage-05-mrp-reread-terminal-state",
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "terminal_states": {"B1": "terminal_landed_hidden_tribunal_blocked"},
                "dependency_graph_edges": [],
                "no_new_resultant_proof": {
                    "proved": True,
                    "basis": "negative fixture: delta/result detail was laundered as terminal state.",
                    "unresolved_burdens": [],
                },
            },
        )
    except HarnessError as exc:
        if "controlled terminal-state heads only" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted delta/result detail as a Stage 05 terminal_state")
    try:
        normalized_stage(
            "stage-05-mrp-reread-terminal-state",
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "terminal_states": {"B1": "landed"},
                "dependency_graph_edges": [],
                "no_new_resultant_proof": True,
                "terminal_state_details": [
                    {
                        "burden_id": "B1",
                        "state": "landed",
                        "basis": [],
                    }
                ],
            },
        )
    except HarnessError as exc:
        if "basis must be a non-empty string or non-empty list" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted empty Stage 05 terminal_state detail basis list")
    stage05_local_record = base_record(
        "self-test-a9-science-source-stage05",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage05",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    stage05_local_record["stages"] = [*replay["stages"][:4], normalized_stage05]
    stage05_local_path = run_dir / "staged-handoff-stage05-model-scope-record.json"
    write_json(stage05_local_path, stage05_local_record)
    validate_replay_record(root, stage05_local_path)

    generated_carried_recurse_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "partial",
            "terminal_states": {"B1": "landed", "B2": "carried-RECURSE"},
            "dependency_graph_edges": [{"from": "B1", "to": "B2"}],
            "generated_burdens": [
                {
                    "burden_id": "B2",
                    "generated_by": "MRP(B1)",
                    "terminal_state": "carried-RECURSE",
                }
            ],
            "per_burden_reread": [
                self_test_reread_generated_entry("B1", "B2"),
                self_test_reread_hold_entry("B2"),
            ],
            "unresolved_burdens": ["B2"],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "B2 was generated by MRP(B1) and remains unexecuted.",
                "unresolved_burdens": ["B2"],
            },
        },
    )
    generated_carried_recurse_record = base_record(
        "self-test-stage05-generated-carried-recurse",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-stage05-generated-carried-recurse",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    generated_carried_recurse_record["stages"] = [*replay["stages"][:4], generated_carried_recurse_stage05]
    generated_carried_recurse_path = run_dir / "stage05-generated-carried-recurse.valid.json"
    write_json(generated_carried_recurse_path, generated_carried_recurse_record)
    validate_replay_record(root, generated_carried_recurse_path)

    rich_stage04_handoff_record = base_record(
        "self-test-stage04-rich-burdens-to-stage05",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-stage04-rich-burdens-to-stage05",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    rich_stage03_detail_map = dict(replay["stages"][2])
    rich_stage03_detail_map["route_target_details"] = {
        "B1": {
            "route_pressure": "source-order diagnostic burden",
            "backing": "self-test detail map keyed by canonical burden id",
        }
    }
    rich_stage04_handoff_record["stages"] = [
        *replay["stages"][:2],
        rich_stage03_detail_map,
        normalized_stage04_rich_burdens,
        normalized_stage05,
    ]
    rich_stage04_handoff_path = run_dir / "stage04-rich-burdens-stage05-handoff.valid.json"
    write_json(rich_stage04_handoff_path, rich_stage04_handoff_record)
    validate_replay_record(root, rich_stage04_handoff_path)

    generated_missing_terminal = dict(stage05_local_record)
    generated_missing_terminal["case_id"] = "self-test-stage05-generated-missing-terminal"
    generated_missing_terminal["model_scope"] = model_scope(
        "self-test-stage05-generated-missing-terminal",
        replay_record,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
    )
    generated_missing_terminal["stages"] = [dict(stage) for stage in stage05_local_record["stages"]]
    generated_missing_terminal["stages"][-1] = dict(generated_missing_terminal["stages"][-1])
    generated_missing_terminal["stages"][-1]["generated_burdens"] = ["B2"]
    generated_missing_terminal_path = run_dir / "stage05-generated-missing-terminal.invalid.json"
    write_json(generated_missing_terminal_path, generated_missing_terminal)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(generated_missing_terminal_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 05 generated burden missing terminal state")

    no_new_with_unresolved = dict(stage05_local_record)
    no_new_with_unresolved["case_id"] = "self-test-stage05-no-new-unresolved"
    no_new_with_unresolved["model_scope"] = model_scope(
        "self-test-stage05-no-new-unresolved",
        replay_record,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
    )
    no_new_with_unresolved["stages"] = [dict(stage) for stage in stage05_local_record["stages"]]
    no_new_with_unresolved["stages"][-1] = dict(no_new_with_unresolved["stages"][-1])
    no_new_with_unresolved["stages"][-1]["unresolved_burdens"] = ["B2"]
    no_new_with_unresolved["stages"][-1]["no_new_resultant_proof"] = True
    no_new_with_unresolved_path = run_dir / "stage05-no-new-unresolved.invalid.json"
    write_json(no_new_with_unresolved_path, no_new_with_unresolved)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(no_new_with_unresolved_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 05 no-new-resultant proof with unresolved burden")

    structured_nar = {
        "n_frame": "science-only-source-order-warrant",
        "live_registers": ["xi", "kappa"],
        "burden_floor": ["B1"],
        "per_burden": [
            {
                "burden_id": "B1",
                "owner_id": "source-status-repair",
                "operation": "source-order-repair",
                "delta_result": "source-order-repaired",
                "mrp_route_result_type": "no_new_resultant",
                "terminal_state": "landed",
                "generation_depth": 0,
            }
        ],
    }
    normalized_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": [
                {
                    "body_ref": "¹B₁",
                    "burden_id": "B1",
                    "owner_id": "source-status-repair",
                    "operation": "source-order-repair",
                    "delta_result": "source-order-repaired",
                    "terminal_state": "landed",
                },
                {
                    "body_ref": "¹B₂",
                    "burden_id": "B1",
                    "owner_id": "M1",
                    "operation": "self-grounding-test",
                    "delta_result": "criterion-self-failed",
                    "terminal_state": "landed",
                }
            ],
            "normalized_activation_record": structured_nar,
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    if normalized_stage06.get("owner_activations") != ["¹B₁", "¹B₂"]:
        raise HarnessError("Self-test failed to normalize Stage 06 owner_activations into body-ref strings")
    if not isinstance(normalized_stage06.get("owner_activation_details"), list):
        raise HarnessError("Self-test failed to preserve Stage 06 owner_activation_details")
    mismatched_route_stage06 = copy.deepcopy(normalized_stage06)
    mismatched_route_stage06["normalized_activation_record"]["per_burden"][0][
        "mrp_route_result_type"
    ] = "generated_burden_instantiation"
    try:
        validate_incremental_handoffs([replay["stages"][3], normalized_stage05, mismatched_route_stage06])
    except HarnessError as exc:
        if "must match stage-05 per_burden_reread route_result_type" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test failed to reject Stage 06 NAR route type mismatch against Stage 05")
    nested_only_nar = dict(structured_nar)
    nested_only_nar["register_deltas"] = {"xi": "source-order-repaired"}
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": nested_only_nar,
            },
        )
    except HarnessError as exc:
        if "register_deltas is required at top level" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted Stage 06 register_deltas nested only under NAR")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                    }
                ],
                "normalized_activation_record": {
                    "n_frame": "science-only-source-order-warrant",
                    "live_registers": ["xi", "kappa"],
                    "burden_floor": ["B1"],
                    "per_burden": [
                        {
                            "burden_id": "B1",
                            "owner_id": "source-status-repair",
                            "operation": "source-order-repair",
                            "delta": ["source-order-repaired"],
                            "terminal_state": "landed",
                        }
                    ],
                },
                "register_deltas": {"xi": ["source-order-repaired"]},
            },
        )
    except HarnessError as exc:
        if "delta_result must be a non-empty owner-local token for SOURCE" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted Stage 06 owner_activation without owner-local delta_result")
    normalized_stage06_list_delta = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁"],
            "normalized_activation_record": structured_nar,
            "register_deltas": [
                {"register": "Omega", "delta": ["B1:model-family-bounded", "B1:predicate-separated"]},
                {"register": "xi", "delta": "B1:source-order-landed"},
            ],
        },
    )
    if normalized_stage06_list_delta["register_deltas"][0]["delta"] != [
        "B1:model-family-bounded",
        "B1:predicate-separated",
    ]:
        raise HarnessError("Self-test failed to preserve Stage 06 list-object register_deltas string lists")
    for invalid_delta, message in [
        ([], "empty string-list"),
        (["B1:source-order-landed", 1], "non-string list member"),
    ]:
        try:
            normalized_stage(
                "stage-06-field-witness-nar",
                {
                    "id": "stage-06-field-witness-nar",
                    "status": "pass",
                    "field_witness_body_refs": ["¹B₁"],
                    "nar_burdens": ["B1"],
                    "owner_activations": ["¹B₁"],
                    "normalized_activation_record": structured_nar,
                    "register_deltas": [{"register": "xi", "delta": invalid_delta}],
                },
            )
        except HarnessError:
            pass
        else:
            raise HarnessError(f"Self-test failed to reject Stage 06 list-object register_deltas {message}")
    normalized_stage06_controlled_delta = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₂", "³B₂"],
            "nar_burdens": ["B1", "B3"],
            "owner_activations": [
                {
                    "body_ref": "¹B₂",
                    "burden_id": "B1",
                    "owner": "M9",
                    "owner_id": "M9",
                    "operation": "predication-repair",
                    "pressure": "selected-predicate-transfer",
                    "delta": "Δ¹B:predicate-separated",
                    "delta_result": "predicate-separated",
                    "land": "Land(¹B)+",
                    "terminal_state": "landed",
                },
                {
                    "body_ref": "³B₂",
                    "burden_id": "B3",
                    "owner": "authority-order-repair",
                    "owner_id": "authority-order-repair",
                    "operation": "sort",
                    "pressure": "proof-text-hidden-support",
                    "delta": "Δ³B:proof-text-hidden-support-blocked",
                    "delta_result": "proof-text-hidden-support-blocked",
                    "land": "Land(³B)+",
                    "terminal_state": "landed",
                },
            ],
            "normalized_activation_record": {
                "n_frame": "selected-do12-source-order-repair",
                "live_registers": ["Omega", "xi"],
                "burden_floor": ["B1", "B3"],
                "per_burden": [
                    {
                        "burden_id": "B1",
                        "owner_id": "M9",
                        "operation": "predication-repair",
                        "pressure": "selected-predicate-transfer",
                        "delta_result": "predicate-separated",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    },
                    {
                        "burden_id": "B3",
                        "owner_id": "authority-order-repair",
                        "operation": "sort",
                        "pressure": "proof-text-hidden-support",
                        "delta_result": "proof-text-hidden-support-blocked",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    },
                ],
            },
            "register_deltas": {"Omega": "predicate-separated", "xi": "proof-text-hidden-support-blocked"},
        },
    )
    delta_details = normalized_stage06_controlled_delta.get("owner_activation_details") or []
    if [item.get("delta_result") for item in delta_details] != [
        "predicate-separated",
        "proof-text-hidden-support-blocked",
    ]:
        raise HarnessError("Self-test failed to preserve exact Stage 06 owner_activation delta_result tokens")
    nar_delta_results = [
        row.get("delta_result")
        for row in normalized_stage06_controlled_delta["normalized_activation_record"]["per_burden"]
    ]
    if nar_delta_results != ["predicate-separated", "proof-text-hidden-support-blocked"]:
        raise HarnessError("Self-test failed to preserve exact Stage 06 NAR delta_result tokens")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₂"],
                "nar_burdens": ["B1"],
                "owner_activations": [
                    {
                        "body_ref": "¹B₂",
                        "burden_id": "B1",
                        "owner": "M9",
                        "owner_id": "M9",
                        "operation": "predication-repair",
                        "pressure": "selected-predicate-transfer",
                        "delta": "Δ¹B:predicate-transfer-blocked",
                        "delta_result": "predicate-transfer-blocked",
                        "land": "Land(¹B)+",
                        "terminal_state": "landed",
                    }
                ],
                "normalized_activation_record": {
                    "n_frame": "selected-do12-source-order-repair",
                    "live_registers": ["Omega"],
                    "burden_floor": ["B1"],
                    "per_burden": [
                        {
                            "burden_id": "B1",
                            "owner_id": "M9",
                            "operation": "predication-repair",
                            "pressure": "selected-predicate-transfer",
                            "delta_result": "predicate-transfer-blocked",
                            "terminal_state": "landed",
                            "generation_depth": 0,
                        }
                    ],
                },
            },
        )
    except HarnessError as exc:
        if "outside controlled vocabulary" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted Stage 06 delta_result laundering")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₃"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₃"],
                "normalized_activation_record": {
                    "n_frame": "selected-source-hidden-support-repair",
                    "live_registers": ["sigma", "xi"],
                    "burden_floor": ["B1"],
                    "per_burden": [
                        {
                            "burden_id": "B1",
                            "owner_id": "authority-order-repair",
                            "operation": "sort",
                            "pressure": "hidden-support-and-source-function-pressure",
                            "delta_result": "authority-order-separated",
                            "terminal_state": "landed",
                            "generation_depth": 0,
                        }
                    ],
                },
            },
        )
    except HarnessError as exc:
        if "hidden-support pressure must use delta_result token 'hidden-support-blocked'" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test accepted Stage 06 NAR hidden-support pressure with authority-order delta")
    stage07_opening_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="opening",
        section_role="visible_opening",
        section_number=1,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "outside\n  `layer_b_act` sections, do not emit any line beginning with `⟦ACT`",
        "Restorative Response, Closing Formulation, or any `⟦ACT` fence",
        "use ordinary prose or bullet text without ACT-row syntax",
    ):
        if required not in stage07_opening_prompt:
            raise HarnessError(f"Self-test Stage 07 opening prompt omitted ACT-fence boundary: {required}")
    stage07_layer_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="layer-a-diagnostic-ir",
        section_role="layer_a_diagnostic_ir",
        section_number=2,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Initial burden set: [¹B]",
        "𝔅_LA (B_LA) = {¹B}",
        "𝔅_MRP (B_MRP) = {}",
        "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}",
        "¹B [xi, kappa] status=initial-live",
        "Do not replace `Initial burden set: [...]` with `Initial burden set ledger:`",
    ):
        if required not in stage07_layer_prompt:
            raise HarnessError(f"Self-test Stage 07 Layer A prompt omitted parser-stable scaffold: {required}")
    stage07_mixed_layer_prompt = release_section_prompt(
        root=root,
        case_name="self-test-mixed-concealment-neutral",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[mixed_concealment_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="layer-a-diagnostic-ir",
        section_role="layer_a_diagnostic_ir",
        section_number=2,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Concealment mode: mixed - irad + juhud pressure",
        "at least two source-owned component pressures",
        "irad, juhud",
        "Do not collapse this to generic `mixed pressure`",
    ):
        if required not in stage07_mixed_layer_prompt:
            raise HarnessError(f"Self-test Stage 07 Layer A mixed-concealment prompt omitted: {required}")
    collapsed_mixed_layer = (
        "Layer A / Diagnostic IR Header\n"
        "Initial burden set: [¹B]\n"
        "𝔅_LA (B_LA) = {¹B}\n"
        "𝔅_MRP (B_MRP) = {}\n"
        "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}\n"
        "Concealment mode: mixed pressure; sincere clarification pressure remains routed to clarification.\n"
    )
    canonical_mixed_layer, mixed_event = canonical_compiled_structural_section(
        "layer_a_diagnostic_ir",
        collapsed_mixed_layer,
        [mixed_concealment_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if not mixed_event:
        raise HarnessError("Self-test Stage 07 mixed concealment canonicalization did not record an event")
    if "Concealment mode: mixed - irad + juhud pressure" not in canonical_mixed_layer:
        raise HarnessError("Self-test Stage 07 mixed concealment canonicalization omitted source-owned components")
    if "Concealment mode: mixed pressure" in canonical_mixed_layer:
        raise HarnessError("Self-test Stage 07 mixed concealment canonicalization left generic mixed pressure")
    if mixed_event.get("source_components") != ["irad", "juhud"]:
        raise HarnessError("Self-test Stage 07 mixed concealment canonicalization metadata missing components")
    stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Stage 07 per-burden MRP visibility contract:",
        "[Mid-Reread Pressure]",
        "Target: ¹B / bounded self-test burden",
        "R(H,Δ): held routes rechecked: none; live remainder: no remaining burden; release/next: STOP after ¹B.",
        "Landed delta: Δ¹B / Delta(B1): bounded-self-test-delta recorded.",
        "Route-gradient: plain-gradient points to STOP after ¹B; no live pressure remains.",
        "Finding: stable",
        "MRP route result type: no_new_resultant",
        "MRP resultant: stable -> no new graph edge; STOP",
        "Graph delta: none",
        "Pre-emption basis: none",
        "Route: STOP",
        "Boundary: T_lang does not imply guaranteed uptake.",
        "Do NOT print any `[Mid-Reread Pressure]` heading or block yourself",
        "print exactly one line-start superscript landing gate per terminal burden",
        "`formal_reread_states[].delta` preserves the public `landed_delta` notation while also carrying machine `Delta(Bn)` identity",
        "ledger-only: print the reconstruction floor",
        "- MRP(¹B): type=no_new_resultant; finding=stable; graph=none; route=STOP",
    ):
        if required not in stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 MRP prompt omitted per-burden scaffold: {required}")
    if "MRP route result type: no_new_resultant." in stage07_mrp_prompt:
        raise HarnessError("Self-test Stage 07 MRP prompt allowed trailing punctuation on no_new_resultant")
    if "terminal states landed; B_MRP empty; no generated burden remains" in stage07_mrp_prompt:
        raise HarnessError("Self-test Stage 07 MRP prompt resurrected the invalid pre-emption literal")
    stage07_act_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-1",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    if canonical_act_row not in stage07_act_prompt:
        raise HarnessError("Self-test Stage 07 ACT prompt omitted exact canonical Stage 04 ACT row")
    for required in (
        "Do not write malformed rows such as `⟦ACT [owner.operation] ...⟧`",
        "Do not write any ACT-looking summary row outside this ACT slice.",
        "¹B₁[source-status-repair] - source-order over scientific-explanations-only-knowledge-source",
        "Contribution-to-Land(¹B)",
        "Land(¹B): summarize the cumulative state delta from the visible submove block(s)",
        "route/context umbrella labels, case-library labels, noetic-frame labels, and code lookups are not load-bearing ACT owners",
        "The `TTP Operation Body:` must visibly perform target -> operation -> result -> contribution",
        "Operation-token discipline: keep the registered callable operation token from the copied ACT row and skeleton.",
        "Delta-layer discipline: the ACT `Δ=` carrier before the colon must be only a burden-state delta such as `Δ¹B` / `ΔB1` or dependency-radius `Δκ`",
        "If the row needs κ/H dependency-radius work, use `Δκ:<owner-local-state-change>`",
        "A compact label such as `reopen-condition-stated` or `scope-boundary-named` cannot replace the visible burden-local state change",
        "Stage07 locality rule: every landed ACT row must make a local proof capsule recoverable near that row",
        "Local proof capsule: make BEFORE, OPERATION, AFTER, DELTA, and LAND-LICENSE recoverable in this block",
        "For every landed row, `Contribution-to-Land(Bn):` must include the local LAND-LICENSE",
        "SOURCE/source-status operation: explicitly sort source authority, source function, proof-stack order, or hidden support",
        "`status` is not a callable ACT operation; use a registered SOURCE operation",
    ):
        if required not in stage07_act_prompt:
            raise HarnessError(f"Self-test Stage 07 ACT prompt omitted semantic scaffold: {required}")
    drifted_visible_act = canonical_act_row.replace("Land(¹B)+", "Land(additional burden 1)+")
    canonical_act_text, canonical_act_event = canonical_compiled_structural_section(
        "layer_b_act",
        "Layer B - Bounded Governed Response\n" + drifted_visible_act + "\n",
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if canonical_act_row not in canonical_act_text or "Land(additional burden 1)" in canonical_act_text:
        raise HarnessError("Self-test Stage 07 ACT canonicalizer did not restore exact Stage 04 row")
    if not canonical_act_event or canonical_act_event.get("canonicalized_visible_act_rows_from_stage04") is not True:
        raise HarnessError("Self-test Stage 07 ACT canonicalizer did not record an event")
    proof_pattern_rows = [
        "⟦ACT ¹B₁[proof-method-audit.proof-family-and-carrier-audit] :: "
        "π=logic-tree-carrier-compression :: body_ref=¹B₁ :: "
        "Δ=Δ¹B:proof-family-carrier-typed :: Land(¹B)+⟧",
        "⟦ACT ¹B₂[pattern-profiling.loaded-label-carrier-audit] :: "
        "π=loaded-label-carrier-compression :: body_ref=¹B₂ :: "
        "Δ=Δ¹B:carrier-function-typed :: Land(¹B)+⟧",
        "⟦ACT ¹B₃[pattern-profiling.proof-packet-reconstruction] :: "
        "π=logic-tree-proof-packet-compression :: body_ref=¹B₃ :: "
        "Δ=Δ¹B:proof-packet-reconstructed :: Land(¹B)+⟧",
    ]
    proof_pattern_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": proof_pattern_rows,
            "act_row_details": self_test_act_row_details(
                proof_pattern_rows,
                {
                    "¹B₁": "μ",
                    "¹B₂": "μ",
                    "¹B₃": "μ",
                },
            ),
        },
    )
    proof_pattern_prompt = release_section_prompt(
        root=root,
        case_name="self-test-proof-pattern-carrier",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, proof_pattern_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-proof-pattern",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁", "¹B₂", "¹B₃"],
    )
    for required in (
        "proof-method-audit.proof-family-and-carrier-audit",
        "premise set, inference grammar, and conclusion scope are no longer treated as a neutral proof",
        "pattern-profiling.loaded-label-carrier-audit",
        "loaded label carrier function is exposed or classified",
        "pattern-profiling.proof-packet-reconstruction",
        "proof packet is reconstructed",
        "the delta token alone is not a state change",
    ):
        if required not in proof_pattern_prompt:
            raise HarnessError(f"Self-test Stage 07 proof/pattern carrier prompt omitted: {required}")
    thin_proof_pattern_layer = "\n".join(
        [
            "## Burden 1 / ¹B — proof carrier compression",
            proof_pattern_rows[0],
            "",
            "### ¹B₁[proof-method-audit] - proof-family-and-carrier-audit over logic-tree-carrier-compression",
            "Target: logic-tree-carrier-compression.",
            "Operation: proof-family-and-carrier-audit audits the logic-tree-carrier-compression with owner family proof-method-audit.",
            "Result/state-change: proof-family-carrier-typed. The logic tree is typed as a conditional proof-carrier.",
            "Contribution-to-Land(¹B): This contributes because the proof carrier no longer gets to hide premise loading inside the formal display.",
            "TTP Operation Body:",
            "The proof-method audit tests the proof family rather than merely naming it. It identifies the premise and predicate set loaded into the diagram, the inference grammar that derives the contradiction, and the conclusion scope the proof claims. The logic tree depends on source sorting and definition stability before it can establish the result.",
            "",
            proof_pattern_rows[1],
            "",
            "### ¹B₂[pattern-profiling] - loaded-label-carrier-audit over loaded-label-carrier-compression",
            "Target: loaded-label-carrier-compression.",
            "Operation: loaded-label-carrier-audit audits the loaded-label-carrier-compression with owner family pattern-profiling.",
            "Result/state-change: carrier-function-typed. The disputed label is typed as a carrier.",
            "Contribution-to-Land(¹B): This submove bounds the carrier function of the label.",
            "TTP Operation Body:",
            "The label functions as a carrier rather than a neutral description. It transmits a hidden proof rule and source-authority posture by compressing the source order, predicate assignment, and conclusion into one loaded phrase. The audit exposes how that carrier function made the contradiction appear settled before the proof was earned.",
            "",
            proof_pattern_rows[2],
            "",
            "### ¹B₃[pattern-profiling] - proof-packet-reconstruction over logic-tree-proof-packet-compression",
            "Target: logic-tree-proof-packet-compression.",
            "Operation: proof-packet-reconstruction reconstructs the logic-tree-proof-packet-compression with owner family pattern-profiling.",
            "Result/state-change: proof-packet-reconstructed. The proof packet is rebuilt in public order.",
            "Contribution-to-Land(¹B): This contributes because the hidden source moves, predicate transfers, and conclusion jump no longer travel inside the diagram.",
            "TTP Operation Body:",
            "The proof-packet reconstruction rebuilds the logic-tree proof packet as an ordered sequence of transfers. It reconstructs the source moves, predicate transfers, and conclusion jump, then exposes the forum switch and carrier compression that made the diagram appear to close before the premises were earned.",
            "Land(¹B): The proof carrier, loaded label carrier, and proof packet reconstruction are all typed.",
            "",
        ]
    )
    canonical_proof_pattern, proof_pattern_event = canonical_compiled_structural_section(
        "layer_b_act",
        thin_proof_pattern_layer,
        [normalized_stage02, proof_pattern_stage04, normalized_stage05, normalized_stage06],
    )
    if not proof_pattern_event or not proof_pattern_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 proof/pattern carrier facet canonicalization did not record an event")
    if "the proof carrier is classified as a proof carrier whose premise set, inference grammar, and conclusion scope are no longer treated as a neutral proof" not in canonical_proof_pattern:
        raise HarnessError("Self-test Stage 07 proof-method carrier canonicalization omitted parser-stable state change")
    if "the loaded label carrier function is exposed and classified" not in canonical_proof_pattern:
        raise HarnessError("Self-test Stage 07 pattern carrier canonicalization omitted parser-stable state change")
    if "licenses Land(¹B) because the loaded label carrier function is exposed and classified" not in canonical_proof_pattern:
        raise HarnessError("Self-test Stage 07 pattern carrier canonicalization omitted parser-stable Land license")
    if "the proof packet is reconstructed so its hidden source moves, predicate transfers, and conclusion jump are exposed" not in canonical_proof_pattern:
        raise HarnessError("Self-test Stage 07 proof-packet canonicalization omitted parser-stable state change")
    if len(proof_pattern_event.get("facet_replacements") or []) != 3:
        raise HarnessError("Self-test Stage 07 proof/pattern carrier canonicalization did not touch all owner facets")
    label_only_proof_pattern = thin_proof_pattern_layer.replace(
        "The proof-method audit tests the proof family rather than merely naming it. It identifies the premise and predicate set loaded into the diagram, the inference grammar that derives the contradiction, and the conclusion scope the proof claims. The logic tree depends on source sorting and definition stability before it can establish the result.",
        "The proof-method-audit owner is named here, so the proof carrier is handled.",
    ).replace(
        "The label functions as a carrier rather than a neutral description. It transmits a hidden proof rule and source-authority posture by compressing the source order, predicate assignment, and conclusion into one loaded phrase. The audit exposes how that carrier function made the contradiction appear settled before the proof was earned.",
        "The pattern-profiling owner is named here, so the carrier is handled.",
    ).replace(
        "The proof-packet reconstruction rebuilds the logic-tree proof packet as an ordered sequence of transfers. It reconstructs the source moves, predicate transfers, and conclusion jump, then exposes the forum switch and carrier compression that made the diagram appear to close before the premises were earned.",
        "The pattern-profiling proof-packet owner is named here, so the proof packet is handled.",
    )
    _, label_only_event = canonical_compiled_structural_section(
        "layer_b_act",
        label_only_proof_pattern,
        [normalized_stage02, proof_pattern_stage04, normalized_stage05, normalized_stage06],
    )
    if label_only_event:
        raise HarnessError("Self-test Stage 07 proof/pattern carrier canonicalization upgraded label-only owner prose")
    proof_route_status_prompt = release_section_prompt(
        root=root,
        case_name="self-test-proof-route-status-public",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, proof_route_status_tau_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-proof-route-status",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    for required in (
        "proof-method-audit.proof-route-status-audit",
        "proof forum, standard of proof, tribunal/burden-function, proof eligibility",
        "premise/inference/conclusion scope are no longer treated as a neutral proof route",
        "Generic proof-route labels do not Land",
    ):
        if required not in proof_route_status_prompt:
            raise HarnessError(f"Self-test Stage 07 proof-route-status prompt omitted: {required}")
    thin_proof_route_status_layer = "\n".join(
        [
            "## Burden 1 / ¹B — proof route status",
            proof_route_status_tau_row,
            "",
            "### ¹B₁[proof-method-audit] - proof-route-status-audit over proof-route-status",
            "Target: proof-route-status.",
            "Operation: proof-route-status-audit audits the proof-route-status with owner family proof-method-audit.",
            "Result/state-change: proof-route-status-clarified.",
            "Contribution-to-Land(¹B): This contributes because the proof forum and burden-function are now bounded.",
            "TTP Operation Body:",
            "The proof-method audit identifies the proof forum, standard of proof, tribunal-function and burden-function that the supporting texts are being made to serve. It names proof eligibility and the premise/inference/conclusion scope so the proof route no longer functions as a neutral proof.",
            "Land(¹B): The proof route status is clarified.",
            "",
        ]
    )
    canonical_proof_route_status, proof_route_status_event = canonical_compiled_structural_section(
        "layer_b_act",
        thin_proof_route_status_layer,
        [normalized_stage02, proof_route_status_tau_stage04, normalized_stage05, normalized_stage06],
    )
    if not proof_route_status_event or not proof_route_status_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 proof-route-status canonicalization did not record an event")
    if "the proof route status is clarified because the proof forum, standard of proof, tribunal/burden-function" not in canonical_proof_route_status:
        raise HarnessError("Self-test Stage 07 proof-route-status canonicalization omitted parser-stable state change")
    label_only_proof_route_status = thin_proof_route_status_layer.replace(
        "The proof-method audit identifies the proof forum, standard of proof, tribunal-function and burden-function that the supporting texts are being made to serve. It names proof eligibility and the premise/inference/conclusion scope so the proof route no longer functions as a neutral proof.",
        "The proof-method-audit proof-route-status-audit owner is named, so the proof route status is handled.",
    )
    _, label_only_proof_route_status_event = canonical_compiled_structural_section(
        "layer_b_act",
        label_only_proof_route_status,
        [normalized_stage02, proof_route_status_tau_stage04, normalized_stage05, normalized_stage06],
    )
    if label_only_proof_route_status_event:
        raise HarnessError("Self-test Stage 07 proof-route-status canonicalization upgraded label-only owner prose")
    fpd_row = (
        "⟦ACT ¹B₁[FPD.foreign-premise-detection] :: "
        "π=imported-criterion-pressure :: body_ref=¹B₁ :: "
        "Δ=Δ¹B:imported-criterion-blocked :: Land(¹B)+⟧"
    )
    fpd_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [fpd_row],
            "act_row_details": self_test_act_row_details([fpd_row], {"¹B₁": "ξ"}),
        },
    )
    fpd_prompt = release_section_prompt(
        root=root,
        case_name="self-test-fpd-public",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, fpd_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-fpd",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    for required in (
        "FPD.foreign-premise-detection",
        "foreign/imported premise, imported criterion, hidden criterion, imported tribunal",
        "Owner labels or generic criterion language do not Land",
        "render HOLD/PARTIAL instead of `Land(Bn)`",
    ):
        if required not in fpd_prompt:
            raise HarnessError(f"Self-test Stage 07 FPD prompt omitted: {required}")
    thin_fpd_layer = "\n".join(
        [
            "## Burden 1 / ¹B — imported criterion pressure",
            fpd_row,
            "",
            "### ¹B₁[FPD] - foreign-premise-detection over imported-criterion-pressure",
            "Target: imported-criterion-pressure.",
            "Operation: foreign-premise-detection audits the imported-criterion-pressure with owner family FPD.",
            "Result/state-change: imported-criterion-blocked.",
            "Contribution-to-Land(¹B): This contributes because the imported criterion can no longer decide the burden from hiding.",
            "TTP Operation Body:",
            "The FPD operation exposes the foreign premise and imported criterion that were functioning as the proof tribunal. It names the hidden criterion and imported tribunal so that criterion can no longer travel as neutral proof.",
            "Land(¹B): The imported criterion is blocked.",
            "",
        ]
    )
    canonical_fpd, fpd_event = canonical_compiled_structural_section(
        "layer_b_act",
        thin_fpd_layer,
        [normalized_stage02, fpd_stage04, normalized_stage05, normalized_stage06],
    )
    if not fpd_event or not fpd_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 FPD canonicalization did not record an event")
    if "Operation: foreign-premise-detection: expose the foreign premise and imported criterion" not in canonical_fpd:
        raise HarnessError("Self-test Stage 07 FPD canonicalization omitted parser-stable operation action")
    if "the foreign premise and imported criterion are exposed" not in canonical_fpd:
        raise HarnessError("Self-test Stage 07 FPD canonicalization omitted parser-stable state change")
    label_only_fpd = thin_fpd_layer.replace(
        "The FPD operation exposes the foreign premise and imported criterion that were functioning as the proof tribunal. It names the hidden criterion and imported tribunal so that criterion can no longer travel as neutral proof.",
        "The FPD owner is named, so the foreign-premise-detection route is handled.",
    ).replace(
        "Land(¹B): The imported criterion is blocked.",
        "Land(¹B): The route is handled.",
    )
    _, label_only_fpd_event = canonical_compiled_structural_section(
        "layer_b_act",
        label_only_fpd,
        [normalized_stage02, fpd_stage04, normalized_stage05, normalized_stage06],
    )
    if label_only_fpd_event:
        raise HarnessError("Self-test Stage 07 FPD canonicalization upgraded label-only owner prose")
    source_split_rows = [
        (
            "⟦ACT ¹B₁[source-status-repair.source-order-repair] :: "
            "π=source-lineage-quotation-order :: body_ref=¹B₁ :: "
            "Δ=Δ¹B:source-order-repaired :: Land(¹B)+⟧"
        ),
        (
            "⟦ACT ¹B₂[authority-order-repair.authority-order-repair] :: "
            "π=authority-rank-tribunal-pressure :: body_ref=¹B₂ :: "
            "Δ=Δ¹B:authority-order-repaired :: Land(¹B)+⟧"
        ),
    ]
    source_split_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁", "¹B₂"],
            "act_rows": source_split_rows,
            "act_row_details": self_test_act_row_details(
                source_split_rows,
                {"¹B₁": "σ", "¹B₂": "σ"},
            ),
        },
    )
    source_split_prompt = release_section_prompt(
        root=root,
        case_name="self-test-source-transition-split",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, source_split_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-source-split",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁", "¹B₂"],
    )
    for required in (
        "SOURCE source-order-repair operation: explicitly order source lineage, quotation",
        "Authority/rank/tribunal/source-sovereignty prose alone is not source-order proof",
        "SOURCE authority-order-repair operation: explicitly order authority, rank",
        "Source-lineage/quotation prose alone is not authority-order proof",
    ):
        if required not in source_split_prompt:
            raise HarnessError(f"Self-test Stage 07 SOURCE split prompt omitted: {required}")
    thin_source_split_layer = "\n".join(
        [
            "## Burden 1 / ¹B — source transition split",
            source_split_rows[0],
            "",
            "### ¹B₁[source-status-repair] - source-order-repair over source-lineage-quotation-order",
            "Target: source-lineage-quotation-order.",
            "Operation: source-order-repair audits the source-lineage-quotation-order with owner family source-status-repair.",
            "Result/state-change: source-order-repaired.",
            "Contribution-to-Land(¹B): This contributes because the source priority and derivation order become explicit.",
            "TTP Operation Body:",
            "The source-order repair distinguishes source lineage, quotation chain, inherited-claim order, source priority, derivation order, and evidential dependency before the burden lands.",
            "",
            source_split_rows[1],
            "",
            "### ¹B₂[authority-order-repair] - authority-order-repair over authority-rank-tribunal-pressure",
            "Target: authority-rank-tribunal-pressure.",
            "Operation: authority-order-repair audits the authority-rank-tribunal-pressure with owner family authority-order-repair.",
            "Result/state-change: authority-order-repaired.",
            "Contribution-to-Land(¹B): This contributes because the rival public authority can no longer act as a higher court.",
            "TTP Operation Body:",
            "The authority-order repair orders authority, rank, tribunal, judging office, source-sovereignty, and public-truth authority before the burden lands.",
            "Land(¹B): the SOURCE transitions land through distinct source-order and authority-order repairs.",
            "",
        ]
    )
    canonical_source_split, source_split_event = canonical_compiled_structural_section(
        "layer_b_act",
        thin_source_split_layer,
        [normalized_stage02, source_split_stage04, normalized_stage05, normalized_stage06],
    )
    if not source_split_event or not source_split_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 SOURCE split facet canonicalization did not record an event")
    if "source-order-repaired; the source lineage, source priority" not in canonical_source_split:
        raise HarnessError("Self-test Stage 07 SOURCE source-order canonicalization omitted source-order state change")
    if "authority-order-repaired; the authority/rank/tribunal relation" not in canonical_source_split:
        raise HarnessError("Self-test Stage 07 SOURCE authority-order canonicalization omitted authority-order state change")
    authority_only_source_order = thin_source_split_layer.split(source_split_rows[1], 1)[0].replace(
        "The source-order repair distinguishes source lineage, quotation chain, inherited-claim order, source priority, derivation order, and evidential dependency before the burden lands.",
        "The source-order repair talks about authority, rank, tribunal, and public-truth authority, but it only repeats authority-order language.",
    )
    _, authority_only_event = canonical_compiled_structural_section(
        "layer_b_act",
        authority_only_source_order,
        [normalized_stage02, source_split_stage04, normalized_stage05, normalized_stage06],
    )
    if authority_only_event:
        raise HarnessError("Self-test Stage 07 SOURCE source-order canonicalization upgraded authority-only prose")
    proof_text_source_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order-repair] :: "
        "π=proof-text-source-order :: body_ref=¹B₁ :: "
        "Δ=Δ¹B:proof-text-hidden-support-blocked :: Land(¹B)+⟧"
    )
    proof_text_source_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁"],
            "act_rows": [proof_text_source_row],
            "act_row_details": self_test_act_row_details(
                [proof_text_source_row],
                {"¹B₁": "σ"},
            ),
        },
    )
    proof_text_source_layer = "\n".join(
        [
            "## Burden 1 / ¹B — proof-text source order",
            proof_text_source_row,
            "",
            "### ¹B₁[source-status-repair] - source-order-repair over proof-text-source-order",
            "Target: proof-text-source-order.",
            "Operation: source-order-repair audits the proof-text-source-order with owner family source-status-repair.",
            "Result/state-change: proof-text-hidden-support-blocked.",
            "Contribution-to-Land(¹B): This contributes because source priority and evidential dependency become explicit.",
            "TTP Operation Body:",
            "The source-order repair distinguishes the proof-text source lineage, quotation chain, inherited-claim order, source priority, derivation order, and evidential dependency before the burden lands.",
            "Land(¹B): proof-text hidden support is blocked by source-order repair.",
            "",
        ]
    )
    canonical_proof_text_source, proof_text_event = canonical_compiled_structural_section(
        "layer_b_act",
        proof_text_source_layer,
        [normalized_stage02, proof_text_source_stage04, normalized_stage05, normalized_stage06],
    )
    if not proof_text_event or not proof_text_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 SOURCE proof-text hidden-support canonicalization did not record an event")
    if "proof-text-hidden-support-blocked" not in canonical_proof_text_source:
        raise HarnessError("Self-test Stage 07 SOURCE proof-text delta was not preserved")
    do_family_rows = [
        (
            "⟦ACT ¹B₁[do-second-loop.punishment-proportionality-accountability] :: "
            "π=eternal-punishment-proportionality-mercy-justice-accountability :: "
            "body_ref=¹B₁ :: Δ=Δ¹B:punishment-proportionality-calibrated :: Land(¹B)+⟧"
        ),
        (
            "⟦ACT ¹B₂[do-attribute-precision.attribute-precision] :: "
            "π=cruelty-inhumanity-kindness-generosity-predication-on-judgment :: "
            "body_ref=¹B₂ :: Δ=Δ¹B:attribute-precision-typed :: Land(¹B)+⟧"
        ),
    ]
    do_family_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_body_refs": ["¹B₁", "¹B₂"],
            "act_rows": do_family_rows,
            "act_row_details": self_test_act_row_details(
                do_family_rows,
                {"¹B₁": "κ", "¹B₂": "Ω"},
            ),
        },
    )
    thin_do_family_layer = "\n".join(
        [
            "## Burden 1 / ¹B — punishment and attribute pressure",
            do_family_rows[0],
            "",
            "### ¹B₁[do-second-loop] - punishment-proportionality-accountability over eternal-punishment-proportionality-mercy-justice-accountability",
            "Target: eternal-punishment-proportionality-mercy-justice-accountability.",
            "Operation: punishment-proportionality-accountability must act on eternal-punishment-proportionality-mercy-justice-accountability with owner family do-second-loop.",
            "Result/state-change: punishment-proportionality-calibrated.",
            "Contribution-to-Land(¹B): This contributes because proportionality is evaluated through accountability instead of raw affective magnitude.",
            "TTP Operation Body:",
            "The do-second-loop operation calibrates punishment proportionality through accountability, warning, knowledge, capacity, record, culpability, mercy, justice, and the Judge's right before the burden lands.",
            "",
            do_family_rows[1],
            "",
            "### ¹B₂[do-attribute-precision] - attribute-precision over cruelty-inhumanity-kindness-generosity-predication-on-judgment",
            "Target: cruelty-inhumanity-kindness-generosity-predication-on-judgment.",
            "Operation: attribute-precision must act on cruelty-inhumanity-kindness-generosity-predication-on-judgment with owner family do-attribute-precision.",
            "Result/state-change: attribute-precision-typed.",
            "Contribution-to-Land(¹B): This contributes because cruelty and kindness predicates are typed before judgment is classified.",
            "TTP Operation Body:",
            "The do-attribute-precision operation types the attribute relation, separates the predicate level, and names the category transfer that would otherwise carry the burden.",
            "Land(¹B): punishment proportionality and attribute precision land locally.",
            "",
        ]
    )
    canonical_do_family, do_family_event = canonical_compiled_structural_section(
        "layer_b_act",
        thin_do_family_layer,
        [normalized_stage02, do_family_stage04, normalized_stage05, normalized_stage06],
    )
    if not do_family_event or not do_family_event.get("canonicalized_owner_transition_facets"):
        raise HarnessError("Self-test Stage 07 DO-family facet canonicalization did not record an event")
    for required in (
        "punishment proportionality is calibrated through accountability, warning, knowledge, capacity, record",
        "attribute-precision operation types the attribute or predicate relation",
    ):
        if required not in canonical_do_family:
            raise HarnessError(f"Self-test Stage 07 DO-family canonicalization omitted: {required}")
    label_only_do_family = thin_do_family_layer.replace(
        "The do-second-loop operation calibrates punishment proportionality through accountability, warning, knowledge, capacity, record, culpability, mercy, justice, and the Judge's right before the burden lands.",
        "The do-second-loop owner is named, so the route is handled.",
    ).replace(
        "The do-attribute-precision operation types the attribute relation, separates the predicate level, and names the category transfer that would otherwise carry the burden.",
        "The do-attribute-precision owner is named, so the route is handled.",
    )
    _, label_only_do_event = canonical_compiled_structural_section(
        "layer_b_act",
        label_only_do_family,
        [normalized_stage02, do_family_stage04, normalized_stage05, normalized_stage06],
    )
    if label_only_do_event:
        raise HarnessError("Self-test Stage 07 DO-family canonicalization upgraded label-only owner prose")
    stage07_m8_prompt = release_section_prompt(
        root=root,
        case_name="self-test-m8-operation",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[
            normalized_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_rows": [
                    "⟦ACT ¹B₁[M8.consequence-trace] :: π=entailment-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:entailment-bounded :: Land(¹B)+⟧"
                ],
                "act_body_refs": ["¹B₁"],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner": "M8",
                        "operation": "consequence-trace",
                        "pressure": "entailment-pressure",
                        "delta": "Δ¹B",
                        "delta_result": "entailment-bounded",
                        "land": "Land(¹B)+",
                    }
                ],
            },
            normalized_stage05,
            normalized_stage06,
        ],
        section_id="act-body-m8",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    for required in (
        "M8 consequence-trace operation: use the registered operation token `consequence-trace`",
        "put result words such as dependency-exposed or entailment-bounded in `Result/state-change:`, not `Operation:`",
        "if the public body cannot state the consequence/dependency, the tested if-accepted implication, and the burden-local state change",
    ):
        if required not in stage07_m8_prompt:
            raise HarnessError(f"Self-test Stage 07 M8 prompt omitted owner scaffold: {required}")
    stage07_m8_dependency_prompt = release_section_prompt(
        root=root,
        case_name="self-test-m8-dependency-operation",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[
            normalized_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_rows": [
                    "⟦ACT ¹B₁[M8.dependency-trace] :: π=dependency-carrier-pressure :: body_ref=¹B₁ :: Δ=Δκ:dependency-exposed :: Land(¹B)+⟧"
                ],
                "act_body_refs": ["¹B₁"],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner": "M8",
                        "operation": "dependency-trace",
                        "pressure": "dependency-carrier-pressure",
                        "delta": "Δκ",
                        "delta_result": "dependency-exposed",
                        "land": "Land(¹B)+",
                    }
                ],
            },
            normalized_stage05,
            normalized_stage06,
        ],
        section_id="act-body-m8-dependency",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    for required in (
        "M8 dependency-trace operation: use the registered operation token `dependency-trace`",
        "the operation-specific delta_result must be `dependency-exposed`",
        "Do not use `entailment-blocked` for dependency-trace",
        "route consequence or entailment-blocking work to `consequence-trace`",
    ):
        if required not in stage07_m8_dependency_prompt:
            raise HarnessError(f"Self-test Stage 07 M8 dependency prompt omitted owner scaffold: {required}")
    stage07_v10_prompt = release_section_prompt(
        root=root,
        case_name="self-test-v10-operation",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[
            normalized_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_rows": [
                    "⟦ACT ¹B₁[V10.provenance-content-authority] :: π=source-provenance-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:transmission-content-vetted :: Land(¹B)+⟧"
                ],
                "act_body_refs": ["¹B₁"],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner": "V10",
                        "operation": "provenance-content-authority",
                        "pressure": "source-provenance-pressure",
                        "delta": "Δ¹B",
                        "delta_result": "transmission-content-vetted",
                        "land": "Land(¹B)+",
                    }
                ],
            },
            normalized_stage05,
            normalized_stage06,
        ],
        section_id="act-body-v10",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    if "V10 provenance/content operation: visibly vet transmission/provenance, content, and authority/status" not in stage07_v10_prompt:
        raise HarnessError("Self-test Stage 07 V10 prompt omitted owner scaffold")
    stage07_attribute_prompt = release_section_prompt(
        root=root,
        case_name="self-test-attribute-operation",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[
            normalized_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_rows": [
                    "⟦ACT ¹B₁[do-attribute-precision.attribute-precision] :: π=person-nature-transfer :: body_ref=¹B₁ :: Δ=Δ¹B:person-nature-transfer-blocked :: Land(¹B)+⟧"
                ],
                "act_body_refs": ["¹B₁"],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner": "do-attribute-precision",
                        "operation": "attribute-precision",
                        "pressure": "person-nature-transfer",
                        "delta": "Δ¹B",
                        "delta_result": "person-nature-transfer-blocked",
                        "land": "Land(¹B)+",
                    }
                ],
            },
            normalized_stage05,
            normalized_stage06,
        ],
        section_id="act-body-attribute",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    if "Attribute-precision operation: type the person/nature or attribute relation" not in stage07_attribute_prompt:
        raise HarnessError("Self-test Stage 07 attribute prompt omitted owner scaffold")
    stage07_restorative_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="restorative-response",
        section_role="restorative_response",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Begin with the exact public role heading `Restorative Response`",
        "Emit that heading exactly once as the first line; do not repeat `Restorative Response`",
        "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint",
        "`Restored criterion/order: ...`",
        "`Relieved pressure: ...`",
        "`Held/scoped/reopenable remainder: ...`",
        "Do not include Closing Formulation here",
    ):
        if required not in stage07_restorative_prompt:
            raise HarnessError(f"Self-test Stage 07 Restorative prompt omitted role-heading scaffold: {required}")
    drifted_restorative_text = (
        "Restorative Response\n\n"
        "The answer restores tawhid and sound reason, but this model-authored prose does not "
        "emit the required held remainder slot.\n"
    )
    canonical_restorative_text, canonical_restorative_event = canonical_compiled_structural_section(
        "restorative_response",
        drifted_restorative_text,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if not canonical_restorative_event:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization did not record an event")
    for required in (
        "Restored criterion/order:",
        "Relieved pressure:",
        "Held/scoped/reopenable remainder:",
    ):
        if required not in canonical_restorative_text:
            raise HarnessError(f"Self-test Stage 07 Restorative canonicalization omitted slot: {required}")
    if canonical_restorative_text.count("Restorative Response") != 1:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization duplicated the heading")
    duplicate_heading_restorative = (
        "Restorative Response\n\n"
        "Restored criterion/order: keep the source-owned order.\n"
        "Relieved pressure: block the proof-stack pressure.\n"
        "Held/scoped/reopenable remainder: future concrete burdens remain reopenable.\n\n"
        "Restorative Response\n"
        "Second restorative tail that must stay body prose, not a second public heading.\n"
    )
    demoted_restorative, demoted_restorative_event = canonical_compiled_structural_section(
        "restorative_response",
        duplicate_heading_restorative,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if not demoted_restorative_event:
        raise HarnessError("Self-test Stage 07 Restorative duplicate heading did not record an event")
    if demoted_restorative.count("Restorative Response") != 1:
        raise HarnessError("Self-test Stage 07 Restorative duplicate heading was not demoted")
    if "Second restorative tail" not in demoted_restorative:
        raise HarnessError("Self-test Stage 07 Restorative duplicate heading demotion dropped body prose")
    if demoted_restorative_event.get("demoted_duplicate_own_section_headings") != 1:
        raise HarnessError("Self-test Stage 07 Restorative duplicate heading metadata missing")
    already_slot_shaped_restorative = (
        "Restorative Response\n\n"
        "Restored criterion/order: keep the source-owned order.\n"
        "Relieved pressure: block the proof-stack pressure.\n"
        "Held/scoped/reopenable remainder: future concrete burdens remain reopenable.\n"
    )
    unchanged_restorative, unchanged_event = canonical_compiled_structural_section(
        "restorative_response",
        already_slot_shaped_restorative,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if unchanged_event or unchanged_restorative != already_slot_shaped_restorative:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization mutated an already slot-shaped section")
    stage07_closing_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="closing-formulation",
        section_role="closing_formulation",
        section_number=8,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    stage07_full_prompt = release_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    stage07_expansion_prompt = release_section_expansion_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        section_id="restorative-response",
        section_role="restorative_response",
        section_min_bytes=1024,
        current_bytes=512,
        expansion_round=1,
        max_rounds=1,
        assigned_body_refs=None,
        existing_text="Restorative Response\n\nHeld/scoped/reopenable remainder: none.\n",
    )
    for label, prompt in {
        "stage07_full": stage07_full_prompt,
        "stage07_v10": stage07_v10_prompt,
        "stage07_restorative": stage07_restorative_prompt,
        "stage07_closing": stage07_closing_prompt,
        "stage07_expansion": stage07_expansion_prompt,
    }.items():
        if "package/provenance" in prompt:
            raise HarnessError(f"Self-test Stage 07 prompt leaked package/provenance shorthand: {label}")
    for required in (
        "Begin with the exact public role heading `Closing Formulation`",
        "Emit that heading exactly once as the first line; do not repeat `Closing Formulation`",
        "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint",
        "`### Established failure`",
        "`### Restored criterion/orientation`",
        "`### Scoped boundary`",
    ):
        if required not in stage07_closing_prompt:
            raise HarnessError(f"Self-test Stage 07 Closing prompt omitted role-heading scaffold: {required}")
    duplicate_heading_closing = (
        "Closing Formulation\n\n"
        "### Established failure\nFailure established.\n"
        "### Restored criterion/orientation\nCriterion restored.\n"
        "### Scoped boundary\nBoundary scoped.\n\n"
        "Closing Formulation\n"
        "Second closing tail that must stay body prose, not a second public heading.\n"
    )
    demoted_closing, demoted_closing_event = canonical_compiled_structural_section(
        "closing_formulation",
        duplicate_heading_closing,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if not demoted_closing_event:
        raise HarnessError("Self-test Stage 07 Closing duplicate heading did not record an event")
    if demoted_closing.count("Closing Formulation") != 1:
        raise HarnessError("Self-test Stage 07 Closing duplicate heading was not demoted")
    if "Second closing tail" not in demoted_closing:
        raise HarnessError("Self-test Stage 07 Closing duplicate heading demotion dropped body prose")
    if demoted_closing_event.get("demoted_duplicate_own_section_headings") != 1:
        raise HarnessError("Self-test Stage 07 Closing duplicate heading metadata missing")
    short_closing = "Closing Formulation\n\nShort governed close.\n"
    supplemented_closing, supplement_event = compiled_section_budget_guardrail(
        "closing_formulation",
        short_closing,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1800,
    )
    if not supplement_event:
        raise HarnessError("Self-test Closing Formulation budget guardrail did not record an event")
    if len(supplemented_closing.encode("utf-8")) < 1800:
        raise HarnessError("Self-test Closing Formulation budget guardrail remained under the byte floor")
    for required in ("### Closure boundary confirmation", "### Burden-state recap", "### Reopenable remainder"):
        if required not in supplemented_closing:
            raise HarnessError(f"Self-test Closing Formulation budget guardrail omitted {required}")
    for forbidden in ("harness", "byte budget", "manifest", "compiler"):
        if forbidden in supplemented_closing:
            raise HarnessError(f"Self-test Closing Formulation budget guardrail leaked harness term {forbidden}")
    unchanged_closing, unchanged_closing_event = compiled_section_budget_guardrail(
        "closing_formulation",
        short_closing + ("Already long enough. " * 120),
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1000,
    )
    if unchanged_closing_event or "### Closure boundary confirmation" in unchanged_closing:
        raise HarnessError("Self-test Closing Formulation budget guardrail mutated an over-floor section")
    short_mrp_terminal = "[Mid-Reread Pressure]\nTarget: MRP(¹B)\n"
    supplemented_mrp, supplemented_mrp_event = compiled_section_budget_guardrail(
        "mrp_reread_terminal",
        short_mrp_terminal,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1600,
    )
    if not supplemented_mrp_event:
        raise HarnessError("Self-test MRP terminal budget guardrail did not record an event")
    if len(supplemented_mrp.encode("utf-8")) < 1600:
        raise HarnessError("Self-test MRP terminal budget guardrail remained under the byte floor")
    for required in (
        "### MRP terminal reconstruction floor",
        "### Route-state ledger",
        "### Stop/Hold boundary",
        "selected burden route",
        "matched owner/TTP floor",
    ):
        if required not in supplemented_mrp:
            raise HarnessError(f"Self-test MRP terminal budget guardrail omitted {required}")
    for forbidden in ("byte budget", "manifest", "compiler", "Khaybar"):
        if forbidden in supplemented_mrp:
            raise HarnessError(f"Self-test MRP terminal budget guardrail leaked implementation/case term {forbidden}")
    short_restorative = "Restorative Response\n\nRestored criterion/order: local route.\n"
    supplemented_restorative, restorative_event = compiled_section_budget_guardrail(
        "restorative_response",
        short_restorative,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1800,
    )
    if not restorative_event:
        raise HarnessError("Self-test Restorative Response budget guardrail did not record an event")
    if len(supplemented_restorative.encode("utf-8")) < 1800:
        raise HarnessError("Self-test Restorative Response budget guardrail remained under the byte floor")
    for required in (
        "### Restorative reconstruction floor",
        "### Restored burden order",
        "### Held/scoped/reopenable remainder",
        "catalogue mass",
    ):
        if required not in supplemented_restorative:
            raise HarnessError(f"Self-test Restorative Response budget guardrail omitted {required}")
    for forbidden in ("byte budget", "manifest", "compiler", "Trinitarian", "Khaybar", "TST", "Secularism"):
        if forbidden in supplemented_restorative:
            raise HarnessError(f"Self-test Restorative Response budget guardrail leaked implementation/case term {forbidden}")
    source_alias_guidance = stage07_field_witness_contract_guidance(
        [
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": "source-family-alias-ordering-self-test",
                "live_registers": ["xi"],
                "burden_floor": ["B1"],
                "burden_floor_details": [{"burden_id": "B1", "register_types": ["xi"]}],
            },
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_burdens": ["B1"],
                "act_targets": ["B1"],
                "act_body_refs": ["B1_1", "B1_2"],
                "act_rows": [
                    "⟦ACT B1_1[source-status-repair.source-order] :: π=source-lineage-order :: body_ref=B1_1 :: Δ=DeltaB1:source-order-repaired :: Land(B1)+⟧",
                    "⟦ACT B1_2[authority-order-repair.sort] :: π=authority-rank-order :: body_ref=B1_2 :: Δ=DeltaB1:authority-order-separated :: Land(B1)+⟧",
                ],
            },
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "terminal_states": {"B1": "landed"},
                "generated_burdens": [],
                "dependency_graph_edges": [],
                "no_new_resultant_proof": {"proved": True, "unresolved_burdens": []},
                "per_burden_reread": [self_test_reread_entry("B1")],
            },
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["B1_1", "B1_2"],
                "nar_burdens": ["B1"],
                "owner_activations": ["B1_1", "B1_2"],
                "normalized_activation_record": {
                    "n_frame": "source-family-alias-ordering-self-test",
                    "live_registers": ["xi"],
                    "burden_floor": ["B1"],
                    "per_burden": [
                        {
                            "burden_id": "B1",
                            "owner_id": "source-status-repair",
                            "operation": "source-order",
                            "delta_result": "source-order-repaired",
                            "terminal_state": "landed",
                            "generation_depth": 0,
                        },
                        {
                            "burden_id": "B1",
                            "owner_id": "authority-order-repair",
                            "operation": "sort",
                            "delta_result": "authority-order-separated",
                            "terminal_state": "landed",
                            "generation_depth": 0,
                        },
                    ],
                },
                "register_deltas": {"xi": ["source-order-repaired", "authority-order-separated"]},
            },
        ]
    )
    for required in (
        '"before_owner": "source-status-repair"',
        '"before_operation": "source-order"',
        '"before_body_ref": "B1_1"',
        '"after_owner": "authority-order-repair"',
        '"after_operation": "sort"',
        '"after_body_ref": "B1_2"',
    ):
        if required not in source_alias_guidance:
            raise HarnessError(f"Self-test SOURCE alias ordering scaffold omitted {required}")
    if re.search(
        r'\{\s*"target": "B1",\s*"before_owner": "source-status-repair",\s*"after_owner": "authority-order-repair"\s*\}',
        source_alias_guidance,
    ):
        raise HarnessError("Self-test SOURCE alias ordering scaffold emitted owner-only alias edge")
    stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Do not set `owner` to `owner.operation`",
        "After Closing Formulation, print the visible Closure/Reconstruction Witness ledger",
        "`field_witness.owner_activation_ordering` must be an object",
        '"owner_activation_ordering"',
        '"policy_id": "diagnostic-ir-pressure-owner-floor-v1"',
        '"ordering_role": "required"',
        "same owner lands multiple operations",
        "`before_operation`, `after_operation`, `before_body_ref`, and `after_body_ref`",
        "repeated same-owner-operation rows need body_ref endpoints",
        "same-owner parallel operations must be listed in `parallel_groups[].members[]`",
        "Do not add unscaffolded `owner_activations[]` rows",
        "visible `𝔅_MRP (B_MRP) = {}` and JSON `\"B_MRP\": []`",
        "JSON machine IDs remain canonical ASCII such as `B1`",
        "`𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required",
        "`coverage_proof.dependency_graph` is required",
        "If the dependency edge list is non-empty",
        "Do not synthesize a generated-burden `MRP(Bn)` row with `graph=none`",
        "Each `nodes[]` burden payload must include `register_types`",
        "one `normalized_activation_record.per_burden[]` row per `owner_activations[]` mirror",
        "plus one MRP-owned row for each generated `B_MRP` burden",
        "`formal_reread_states[]` is required",
        "machine `field_witness` JSON, NAR rows, and optional sidecars as separate clone states",
        "The line `field_witness` is only a marker",
        "`body_ref` remains the bare join key copied from ACT",
        "`land` and `land_target` are witness mirrors of visible `Land(Bn)` clauses",
        "`curl_state` values must be parser-stable JSON strings",
        'emit JSON string `"null"`, never bare JSON null',
        "Terminal `STOP` / `no_new_resultant` rows must set",
        '"curl_state": "null"',
        '"B_MRP": []',
        '"dependency_graph"',
        '"formal_reread_states"',
        '"source_burden": "B1"',
        '"route_result_type": "no_new_resultant"',
        '"graph_delta": "none"',
        '"route": "STOP"',
        '"no_new_resultant_proof"',
        '"register_types": [\n        "xi",\n        "kappa"\n      ]',
        '"target": "B1"',
        '"generation_depth": 0',
        '"owner": "source-status-repair"',
        '"operation": "source-order"',
    ):
        if required not in stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 field_witness prompt omitted mirror scaffold: {required}")
    stage07_id_alias_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-id-alias-kappa-coverage",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[id_alias_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    if '"kappa": [\n          "B3"\n        ]' not in stage07_id_alias_witness_prompt:
        raise HarnessError("Self-test Stage 07 scaffold lost kappa diagnostic coverage from Stage 02 id alias")
    stage07_kappa_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-kappa-carrier",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[
            normalized_stage02,
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_rows": [
                    "⟦ACT ¹B₁[M8.consequence-trace] :: π=entailment-pressure :: body_ref=¹B₁ :: Δ=Δκ:entailment-blocked :: Land(¹B)+⟧"
                ],
                "act_body_refs": ["¹B₁"],
                "act_row_details": [
                    {
                        "body_ref": "¹B₁",
                        "burden_id": "B1",
                        "owner": "M8",
                        "operation": "consequence-trace",
                        "pressure": "entailment-pressure",
                        "delta": "Δκ",
                        "delta_result": "entailment-blocked",
                        "land": "Land(¹B)+",
                    }
                ],
            },
            normalized_stage05,
            normalized_stage06,
        ],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=9,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    kappa_primary_scaffold = stage07_kappa_witness_prompt.split(
        "- Mirror these exact ACT-visible values by body_ref;",
        1,
    )[0]
    for required in (
        "whose `delta` carrier is `Δκ` / `Delta-kappa`",
        '"kappa_carrier": "κ dependency-radius carrier for ¹B₁ over entailment-pressure"',
        '"dependency_radius": "B1 dependency radius after consequence-trace"',
        '"reread_state_effect": "R(H,Delta) binds Δκ back to B1 before release"',
    ):
        if required not in stage07_kappa_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 field_witness prompt omitted kappa carrier scaffold: {required}")
        if required.startswith('"') and required not in kappa_primary_scaffold:
            raise HarnessError(f"Self-test Stage 07 primary field_witness scaffold omitted kappa carrier field: {required}")
    stage07_full_release_prompt = release_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    for required in (
        "Stage07 checker-owned field_witness/NAR clone-state contract:",
        "Stage 07 field_witness mirror contract:",
        "`field_witness.owner_activation_ordering` must be an object",
        '"owner_activation_ordering"',
        '"policy_id": "diagnostic-ir-pressure-owner-floor-v1"',
        '"ordering_role": "required"',
        "Do not add unscaffolded `owner_activations[]` rows",
        "For every `owner_activations[]` mirror whose `delta` carrier is `Δκ` / `Delta-kappa`",
        "`coverage_proof.diagnostic_completeness.live_registers`",
        "`normalized_activation_record.per_burden[]`",
        "Per-burden MRP record-surface contract (parity-validated):",
        "print exactly one `[Mid-Reread Pressure]` block rendered VERBATIM",
        "Do not invent, merge, or rephrase pressure-activation slots",
        "Do not summarize the per-burden rereads into one terminal closure block",
        "stop and return a held/failed status rather than fabricating block content",
        "any divergence fails Stage 07 release validation",
        "Block for Land(¹B): print exactly:",
        "Target: ¹B / bounded self-test burden",
    ):
        if required not in stage07_full_release_prompt:
            raise HarnessError(f"Self-test Stage 07 release prompt omitted witness clone-state scaffold: {required}")
    generated_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "held",
            "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
            "dependency_graph_edges": [
                {"source": "B1", "target": "B2", "type": "generated_burden_instantiation", "via": "MRP(B1)"}
            ],
            "generated_burdens": [
                {
                    "burden_id": "B2",
                    "generated_by": "MRP(B1)",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": "self-test generated boundary remains live",
                }
            ],
            "reread_state": {
                "source_burden": "B1",
                "route_result_type": "generated_burden_instantiation",
                "route": "RECURSE",
            },
            "per_burden_reread": [
                self_test_reread_generated_entry("B1", "B2"),
                self_test_reread_hold_entry("B2"),
            ],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "self-test generated B2 remains unresolved",
                "unresolved_burdens": ["B2"],
            },
            "unresolved_burdens": ["B2"],
        },
    )
    generated_stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-generated-burden",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, generated_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "¹B (root); ¹B → ²B",
        "²B: held-with-reason / MRP(¹B) / no Stage 04 ACT rows",
        "MRP(¹B): type=generated_burden_instantiation; finding=genuine-dependent; graph=¹B → ²B; route=RECURSE",
        "𝒞(Ψᴺ): HOLD / coverage_complete=false; unresolved_burdens=[B2]",
        '"B_MRP": [\n    "B2"\n  ]',
        '"generated_burdens"',
        '"id": "B2"',
        '"generated_by": "MRP(B1)"',
        '"burden_id": "B2"',
        '"owner_id": "MRP"',
        '"operation": "generated_burden_instantiation"',
        '"coverage_complete": false',
        '"proved": false',
        "explicit HOLD/PARTIAL accounting",
        "visible public MRP source set, Closure/Reconstruction Witness `MRP(...)` rows, JSON `mrp_resultants[]`, and JSON `formal_reread_states[]` must be exactly the same source set",
    ):
        if required not in generated_stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 generated-burden prompt omitted scaffold: {required}")
    if "MRP(B2): type=generated_burden_instantiation" in generated_stage07_witness_prompt:
        raise HarnessError("Self-test Stage 07 generated-burden prompt synthesized an MRP(B2) graph=none row")
    wide_per_burden_entries = [
        self_test_reread_entry("B1", next_burden_id="B2"),
        self_test_reread_entry("B2", next_burden_id="B3"),
        self_test_reread_entry("B3", next_burden_id="B4"),
        self_test_reread_entry("B4", next_burden_id="B5"),
        self_test_reread_generated_entry("B5", "B6"),
        self_test_reread_hold_entry("B6"),
    ]
    wide_states = stage07_formal_reread_states(
        wide_per_burden_entries,
        {"B1": "landed", "B2": "landed", "B3": "landed", "B4": "landed", "B5": "landed", "B6": "carried-RECURSE"},
        unresolved_burdens=["B6"],
    )
    if [row.get("source_burden") for row in wide_states] != ["B1", "B2", "B3", "B4", "B5", "B6"]:
        raise HarnessError("Self-test Stage 07 wide MRP formal reread states did not preserve B1-B6 source registration")
    if any(row.get("curl_state") != "null" for row in wide_states[:4]):
        raise HarnessError("Self-test Stage 07 wide MRP landed formal reread states emitted non-string/null curl_state")
    for row, entry in zip(wide_states, wide_per_burden_entries):
        if row.get("delta") != stage07_formal_delta(entry["landed_delta"], str(entry.get("burden_id") or "")):
            raise HarnessError("Self-test Stage 07 formal reread states did not preserve landed_delta with machine identity")
        expected_route_gradient = stage07_formal_route_gradient(
            entry,
            str(entry.get("route_result_type") or ""),
            stage07_route_target_from_graph(entry.get("graph_delta")),
        )
        if row.get("route_gradient") != expected_route_gradient:
            raise HarnessError("Self-test Stage 07 formal reread states did not preserve formal route_gradient projection")
        if row.get("preemption_basis") != entry["preemption_basis"]:
            raise HarnessError("Self-test Stage 07 formal reread states did not mirror per_burden_reread preemption_basis 1:1")
        if row.get("mrp_resultant") != entry["mrp_resultant"]:
            raise HarnessError("Self-test Stage 07 formal reread states did not mirror per_burden_reread mrp_resultant 1:1")
    held_identity_entry = self_test_reread_entry(
        "B2",
        next_burden_id="B3",
        route_gradient=(
            "∇ route: predication/scope repair reduces contradiction pressure but routes "
            "remaining compression pressure to the proof-carrier audit."
        ),
    )
    held_identity_state = stage07_formal_reread_states(
        [held_identity_entry],
        {"B2": "landed", "B3": "landed"},
    )[0]
    held_identity_gradient = str(held_identity_state.get("route_gradient") or "")
    if "already-held B3 from B_LA" not in held_identity_gradient:
        raise HarnessError("Self-test Stage 07 held route_gradient did not add raw B3/B_LA identity")
    b6_state = wide_states[-1]
    if b6_state.get("divergence_state") != "non-neutral" or b6_state.get("curl_state") != "held":
        raise HarnessError("Self-test Stage 07 B6 held row did not mirror the per-burden non-neutral/held field diagnostics")
    if b6_state.get("route_result_type") != "hold_partial" or b6_state.get("route") != "HOLD":
        raise HarnessError("Self-test Stage 07 B6 held row did not preserve HOLD/hold_partial accounting")
    if "no_new_resultant_proof" in b6_state:
        raise HarnessError("Self-test Stage 07 B6 held row attached a terminal STOP proof to a held burden")
    if "plain-gradient holds ⁶B as HOLD/PARTIAL" not in str(b6_state.get("route_gradient")):
        raise HarnessError("Self-test Stage 07 B6 held row omitted public-token HOLD/PARTIAL route-gradient")
    stop_display_entry = self_test_reread_entry(
        "B1",
        divergence="∇·B: settled / visible public wording remains richer than the machine row",
        landed_delta="Δ¹B: glyph-only public delta before formal projection",
    )
    stop_display_states = stage07_formal_reread_states([stop_display_entry], {"B1": "landed"})
    stop_display_state = stop_display_states[0]
    if stop_display_state.get("divergence_state") != "neutral":
        raise HarnessError("Self-test Stage 07 STOP formal reread state did not normalize settled/bounded divergence to neutral")
    if "Delta(B1)" not in str(stop_display_state.get("delta")):
        raise HarnessError("Self-test Stage 07 STOP formal reread state did not add machine Delta(B1) identity")
    non_neutral_stop_entry = self_test_reread_entry(
        "B1",
        divergence="∇·B: non-neutral / visible public wording names the exposed framework before terminal STOP",
    )
    non_neutral_stop_state = stage07_formal_reread_states([non_neutral_stop_entry], {"B1": "landed"})[0]
    if non_neutral_stop_state.get("divergence_state") != "neutral":
        raise HarnessError("Self-test Stage 07 STOP formal reread state did not normalize non-neutral divergence to neutral")
    resolved_stop_entry = self_test_reread_entry(
        "B1",
        curl="∇×κ: resolved / visible public wording says the loop is resolved",
    )
    resolved_stop_state = stage07_formal_reread_states([resolved_stop_entry], {"B1": "landed"})[0]
    if resolved_stop_state.get("curl_state") != "null":
        raise HarnessError("Self-test Stage 07 STOP formal reread state did not normalize resolved curl to null")
    held_display_stop_entry = self_test_reread_entry(
        "B1",
        curl="∇×κ: held / visible public wording names a bounded held-route boundary",
    )
    held_display_stop_state = stage07_formal_reread_states([held_display_stop_entry], {"B1": "landed"})[0]
    if held_display_stop_state.get("curl_state") != "null":
        raise HarnessError("Self-test Stage 07 STOP formal reread state did not normalize held curl to null")
    unresolved_stop_states = stage07_formal_reread_states(
        [self_test_reread_entry("B6")],
        {"B6": "carried-RECURSE"},
        unresolved_burdens=["B6"],
    )
    unresolved_stop_proof = unresolved_stop_states[0].get("no_new_resultant_proof")
    if not isinstance(unresolved_stop_proof, dict) or unresolved_stop_proof.get("proved") is not False:
        raise HarnessError("Self-test Stage 07 unresolved STOP projection claimed a clean no-new-resultant proof")
    wide_stage02 = dict(normalized_stage02)
    wide_stage02["burden_floor"] = ["B1", "B2", "B3", "B4", "B5"]
    wide_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "partial",
            "terminal_states": {
                "B1": "landed",
                "B2": "landed",
                "B3": "landed",
                "B4": "landed",
                "B5": "landed",
                "B6": "carried-RECURSE",
            },
            "dependency_graph_edges": [
                {"source": "B1", "target": "B2", "type": "held_burden_activation"},
                {"source": "B2", "target": "B3", "type": "held_burden_activation"},
                {"source": "B3", "target": "B4", "type": "held_burden_activation"},
                {"source": "B4", "target": "B5", "type": "held_burden_activation"},
                {"source": "B5", "target": "B6", "type": "generated_burden_instantiation"},
            ],
            "generated_burdens": [
                {
                    "burden_id": "B6",
                    "generated_by": "MRP(B5)",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": "self-test generated burden remains live",
                }
            ],
            "per_burden_reread": [
                self_test_reread_entry("B1", next_burden_id="B2"),
                self_test_reread_entry("B2", next_burden_id="B3"),
                self_test_reread_entry("B3", next_burden_id="B4"),
                self_test_reread_entry("B4", next_burden_id="B5"),
                self_test_reread_generated_entry("B5", "B6"),
                self_test_reread_hold_entry("B6"),
            ],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "self-test generated B6 remains unresolved",
                "unresolved_burdens": ["B6"],
            },
            "unresolved_burdens": ["B6"],
        },
    )
    wide_stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-wide-generated-chain",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "The harness injects one canonical `[Mid-Reread Pressure]` block immediately after each line-start superscript `Land(ⁿB):` landing gate",
        "Do NOT print any `[Mid-Reread Pressure]` heading or block yourself",
        "Every landing gate must match one Stage 05 per_burden_reread record",
        "Target: ¹B / bounded self-test burden",
        "Target: ²B / bounded self-test burden",
        "Target: ³B / bounded self-test burden",
        "Target: ⁴B / bounded self-test burden",
        "Target: ⁵B / bounded self-test burden",
        "Target: ⁶B / bounded self-test burden",
        "MRP route result type: generated_burden_instantiation",
        "MRP route result type: hold_partial",
        "Route: HOLD",
        "- MRP(⁶B): type=hold_partial; finding=partial-real; graph=none; route=HOLD",
        "ledger-only: print the reconstruction floor",
    ):
        if required not in wide_stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 wide MRP prompt omitted scaffold: {required}")
    wide_stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-wide-generated-chain",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        '"source_burden": "B6"',
        '"route_result_type": "hold_partial"',
        '"route": "HOLD"',
        '"curl_state": "null"',
        '"curl_state": "held"',
        '"coverage_complete": false',
        '"id": "B6"',
        '"generated_by": "MRP(B5)"',
    ):
        if required not in wide_stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 wide field_witness prompt omitted scaffold: {required}")

    def synthetic_act_row(burden: str) -> str:
        number = burden[1:]
        public = public_burden_id(burden)
        body_ref = f"{public}₁"
        return (
            f"⟦ACT {body_ref}[M8.trace] :: π=pressure-{number} :: "
            f"body_ref={body_ref} :: Δ=Δ{public}:consequence-traced :: Land({public})+⟧"
        )

    def synthetic_stage04(burdens: list[str]) -> dict[str, Any]:
        rows = [synthetic_act_row(burden) for burden in burdens]
        axis_by_ref = {
            parsed_stage04_act_detail(row)["body_ref"]: "κ"
            for row in rows
            if parsed_stage04_act_detail(row)
        }
        return normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": burdens,
                "act_burdens": burdens,
                "act_rows": rows,
                "act_row_details": self_test_act_row_details(rows, axis_by_ref),
            },
        )

    baseline_held_stage02 = dict(normalized_stage02)
    baseline_held_stage02["burden_floor"] = ["B1", "B2", "B3"]
    baseline_held_stage02["burden_floor_details"] = [
        {"burden_id": "B1", "register_types": ["xi"]},
        {"burden_id": "B2", "register_types": ["kappa"]},
        {"burden_id": "B3", "register_types": ["mu"]},
    ]
    baseline_held_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "partial",
            "terminal_states": {
                "B1": "landed",
                "B2": "held-with-reason",
                "B3": "landed",
            },
            "dependency_graph_edges": [],
            "reread_state": {
                "source_burden": "B3",
                "route_result_type": "no_new_resultant",
                "route": "STOP",
            },
            "per_burden_reread": [
                self_test_reread_entry("B1"),
                self_test_reread_hold_entry("B2"),
                self_test_reread_entry("B3"),
            ],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "baseline B_LA burden remains held; whole-field STOP is not licensed",
                "unresolved_burdens": ["B2"],
            },
            "unresolved_burdens": ["B2"],
        },
    )
    baseline_held_stages = [
        baseline_held_stage02,
        synthetic_stage04(["B1", "B2", "B3"]),
        baseline_held_stage05,
        normalized_stage06,
    ]
    baseline_held_mrp_text = stage07_mrp_reread_section_scaffold(baseline_held_stages)
    baseline_held_witness_text = stage07_field_witness_section_scaffold(baseline_held_stages)
    baseline_held_payload = first_json_object_from_text(
        baseline_held_witness_text.split("\nfield_witness\n", 1)[-1]
    )
    if baseline_held_payload is None:
        raise HarnessError("Self-test baseline-held canary did not emit field_witness JSON")
    for required in (
        "MRP terminal reconstruction floor:",
        "- MRP(²B): type=hold_partial; finding=partial-real; graph=none; route=HOLD",
        "²B: held-with-reason",
    ):
        if required not in baseline_held_mrp_text:
            raise HarnessError(f"Self-test baseline-held MRP ledger omitted scaffold: {required}")
    if "[Mid-Reread Pressure]" in baseline_held_mrp_text:
        raise HarnessError("Self-test baseline-held MRP ledger must stay ledger-only without heading blocks")
    if "coverage_complete=false; unresolved_burdens=[B2]" not in baseline_held_witness_text:
        raise HarnessError("Self-test baseline-held witness omitted coverage_complete=false for B2")
    if "b_la_hold_open=[B2]" not in baseline_held_witness_text:
        raise HarnessError("Self-test baseline-held witness omitted B_LA hold-open curl marker for B2")
    if "generated_burden_hold=[B2]" in baseline_held_witness_text:
        raise HarnessError("Self-test baseline-held witness mislabeled B_LA hold as generated_burden_hold")
    baseline_held_states = [
        row for row in baseline_held_payload.get("formal_reread_states", [])
        if isinstance(row, dict)
    ]
    b2_state = next((row for row in baseline_held_states if row.get("source_burden") == "B2"), None)
    if not b2_state:
        raise HarnessError("Self-test baseline-held canary omitted B2 formal reread state")
    if b2_state.get("route_result_type") != "hold_partial" or b2_state.get("route") != "HOLD":
        raise HarnessError("Self-test baseline-held canary did not preserve the held HOLD/PARTIAL record")
    if b2_state.get("divergence_state") != "non-neutral" or b2_state.get("curl_state") != "held":
        raise HarnessError("Self-test baseline-held canary did not mirror non-neutral/held diagnostics")
    if "no_new_resultant_proof" in b2_state:
        raise HarnessError("Self-test baseline-held canary attached terminal STOP proof to held burden")
    if any(
        row.get("route_result_type") == "no_new_resultant"
        and isinstance(row.get("no_new_resultant_proof"), dict)
        and row["no_new_resultant_proof"].get("stop_licensed") is True
        for row in baseline_held_states
    ):
        raise HarnessError("Self-test baseline-held canary left a clean STOP proof while B2 remained held")
    if baseline_held_payload.get("coverage_proof", {}).get("coverage_complete") is not False:
        raise HarnessError("Self-test baseline-held canary falsely completed coverage")

    generated_topology_stage02 = {
        "id": "stage-02-layer-a-diagnostic-ir",
        "status": "pass",
        "selected_n_frame": "self-test-generated-topology",
        "live_registers": ["xi", "kappa"],
        "burden_floor": ["B1", "B2", "B3", "B4", "B5"],
        "burden_floor_details": [
            {"burden_id": "B1", "register_types": ["xi"]},
            {"burden_id": "B2", "register_types": ["kappa"]},
            {"burden_id": "B3", "register_types": ["xi"]},
            {"burden_id": "B4", "register_types": ["kappa"]},
            {"burden_id": "B5", "register_types": ["xi", "kappa"]},
        ],
    }

    def synthetic_generated_stage05(parent: str, generated: str, *, executed: bool) -> dict[str, Any]:
        terminal_states = {burden: "landed" for burden in generated_topology_stage02["burden_floor"]}
        terminal_states[generated] = "landed" if executed else "carried-RECURSE"
        payload: dict[str, Any] = {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass" if executed else "partial",
            "terminal_states": terminal_states,
            "dependency_graph_edges": [
                {
                    "from": parent,
                    "to": generated,
                    "source": f"MRP({parent})",
                    "type": "generated_burden_instantiation",
                }
            ],
            "generated_burdens": [
                {
                    "burden_id": generated,
                    "generated_by": f"MRP({parent})",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": f"self-test {parent} generated {generated}",
                }
            ],
            "reread_state": {
                "source_burden": generated if executed else parent,
                "route_result_type": "no_new_resultant" if executed else "generated_burden_instantiation",
                "route": "STOP" if executed else "RECURSE",
            },
            "per_burden_reread": [
                *(
                    self_test_reread_entry(burden)
                    for burden in generated_topology_stage02["burden_floor"]
                    if burden != parent
                ),
                self_test_reread_generated_entry(parent, generated),
                (
                    self_test_reread_entry(generated)
                    if executed
                    else self_test_reread_hold_entry(generated)
                ),
            ],
        }
        if executed:
            payload["no_new_resultant_proof"] = {
                "proved": True,
                "basis": "generated burden was actually executed and landed in Stage 04",
                "unresolved_burdens": [],
            }
            payload["unresolved_burdens"] = []
        else:
            payload["no_new_resultant_proof"] = {
                "proved": False,
                "basis": "generated burden remains unresolved and carried",
                "unresolved_burdens": [generated],
            }
            payload["unresolved_burdens"] = [generated]
        return normalized_stage("stage-05-mrp-reread-terminal-state", payload)

    restoration_track_record = {
        "id": "B2",
        "generated_by": "MRP(B1)",
        "escape_routes_checked": [{"type": "restoration-recoil", "live": True, "target": "B2"}],
    }
    if generated_burden_track(restoration_track_record, ["generated_burden_instantiation"]) != "restoration":
        raise HarnessError("Self-test failed to derive generated restoration track from structured escape route")
    prose_only_track_record = {
        "id": "B2",
        "generated_by": "MRP(B1)",
        "title": "restoration recoil remains in prose only",
        "reason": "restoration is mentioned without a structured route object",
    }
    if generated_burden_track(prose_only_track_record):
        raise HarnessError("Self-test derived generated track from prose-only restoration wording")
    if generated_burden_track({"id": "B2", "generated_by": "MRP(B1)"}, ["generated_burden_instantiation"]) != "primary":
        raise HarnessError("Self-test failed to derive primary generated track from typed generated route")

    def assert_generated_topology(parent: str, generated: str, *, executed: bool, label: str) -> None:
        stage04 = synthetic_stage04([*generated_topology_stage02["burden_floor"], *([generated] if executed else [])])
        stage05 = synthetic_generated_stage05(parent, generated, executed=executed)
        stages_for_case = [generated_topology_stage02, stage04, stage05, normalized_stage06]
        mrp_text = stage07_mrp_reread_section_scaffold(stages_for_case)
        witness_text = stage07_field_witness_section_scaffold(stages_for_case)
        payload = first_json_object_from_text(witness_text)
        if payload is None:
            raise HarnessError(f"Self-test {label} generated topology did not emit field_witness JSON")
        if generated not in payload.get("B_MRP", []):
            raise HarnessError(f"Self-test {label} generated burden {generated} missing from B_MRP")
        if generated in payload.get("B_LA", []):
            raise HarnessError(f"Self-test {label} generated burden {generated} was misclassified as B_LA")
        if parent not in payload.get("B_LA", []):
            raise HarnessError(f"Self-test {label} parent {parent} must remain a baseline B_LA burden")
        generated_records = {
            str(item.get("id") or item.get("burden_id")): item
            for item in payload.get("generated_burdens", [])
            if isinstance(item, dict)
        }
        record = generated_records.get(generated)
        if not isinstance(record, dict) or record.get("generated_by") != f"MRP({parent})":
            raise HarnessError(f"Self-test {label} generated_burdens provenance missing MRP({parent})")
        if record.get("track") not in GENERATED_MRP_TRACKS:
            raise HarnessError(f"Self-test {label} generated_burdens track missing or non-canonical")
        edge = {"from": parent, "to": generated}
        coverage_edges = payload.get("coverage_proof", {}).get("dependency_graph", {}).get("edges", [])
        if edge not in coverage_edges:
            raise HarnessError(f"Self-test {label} dependency graph missing {parent}->{generated}")
        if not any(item.get("source") == parent and item.get("type") == "generated_burden_instantiation" for item in payload.get("mrp_resultants", [])):
            raise HarnessError(f"Self-test {label} MRP resultants missing generated source {parent}")
        public_marker = f"## Burden {generated[1:]} / {public_burden_id(generated)} [generated-by: MRP({public_burden_id(parent)})]"
        if public_marker not in mrp_text:
            raise HarnessError(f"Self-test {label} public generated marker missing")
        later_baselines = [
            burden
            for burden in generated_topology_stage02["burden_floor"]
            if int(burden[1:]) > int(parent[1:])
        ]
        for later in later_baselines:
            if later not in payload.get("B_LA", []):
                raise HarnessError(f"Self-test {label} later baseline {later} fell out of B_LA")
        coverage_complete = payload.get("coverage_proof", {}).get("coverage_complete")
        if executed:
            if coverage_complete is not True:
                raise HarnessError(f"Self-test {label} executed generated branch did not complete coverage")
            if f"Land({public_burden_id(generated)})" not in mrp_text:
                raise HarnessError(f"Self-test {label} executed generated branch did not render Land({generated})")
            activations = [
                item for item in payload.get("owner_activations", [])
                if isinstance(item, dict) and item.get("target") == generated
            ]
            if not activations or activations[0].get("source") != f"MRP({parent})":
                raise HarnessError(f"Self-test {label} executed generated branch lacked MRP(parent) owner activation")
        else:
            if coverage_complete is not False:
                raise HarnessError(f"Self-test {label} held generated branch falsely completed coverage")
            if f"HOLD({public_burden_id(generated)})" not in mrp_text:
                raise HarnessError(f"Self-test {label} held generated branch did not render HOLD({generated})")
            activations = [
                item for item in payload.get("owner_activations", [])
                if isinstance(item, dict) and item.get("target") == generated
            ]
            if activations:
                raise HarnessError(f"Self-test {label} held generated branch invented owner activations")

    def assert_generated_edge_normalized(edge_type: str | None, label: str) -> None:
        stage05 = synthetic_generated_stage05("B3", "B6", executed=False)
        edge = stage05["dependency_graph_edges"][0]
        if edge_type is None:
            edge.pop("type", None)
        else:
            edge["type"] = edge_type
        edges = stage05_dependency_edges(stage05)
        if not edges or edges[0].get("type") != "generated_burden_instantiation":
            raise HarnessError(f"Self-test {label} did not normalize generated B_MRP edge to generated_burden_instantiation")
        stages_for_case = [
            generated_topology_stage02,
            synthetic_stage04(generated_topology_stage02["burden_floor"]),
            stage05,
            normalized_stage06,
        ]
        payload = first_json_object_from_text(stage07_field_witness_section_scaffold(stages_for_case))
        if payload is None:
            raise HarnessError(f"Self-test {label} did not emit field_witness JSON")
        resultants = [
            row for row in payload.get("mrp_resultants", [])
            if isinstance(row, dict) and row.get("source") == "B3"
        ]
        if not resultants or resultants[0].get("type") != "generated_burden_instantiation":
            raise HarnessError(f"Self-test {label} left generated B_MRP source misclassified in mrp_resultants")
        states = [
            row for row in payload.get("formal_reread_states", [])
            if isinstance(row, dict) and row.get("source_burden") == "B3"
        ]
        if not states or states[0].get("route_result_type") != "generated_burden_instantiation":
            raise HarnessError(f"Self-test {label} left generated B_MRP source misclassified in formal_reread_states")

    assert_generated_edge_normalized(None, "generated-edge-missing-type")
    assert_generated_edge_normalized("held_burden_activation", "generated-edge-held-type")
    assert_generated_topology("B1", "B6", executed=False, label="early-held")
    assert_generated_topology("B3", "B6", executed=False, label="mid-held")
    assert_generated_topology("B5", "B6", executed=False, label="terminal-held")
    assert_generated_topology("B3", "B6", executed=True, label="mid-executed")
    false_closed_generated_stage05 = copy.deepcopy(synthetic_generated_stage05("B3", "B6", executed=False))
    false_closed_generated_stage05["terminal_states"]["B6"] = "landed"
    false_closed_generated_stage05["unresolved_burdens"] = []
    false_closed_generated_stage05["no_new_resultant_proof"] = {
        "proved": True,
        "basis": "negative fixture: generated burden was not executed but claimed clean terminal closure",
        "unresolved_burdens": [],
    }
    false_closed_generated_stage05["reread_state"] = {
        "source_burden": "B6",
        "route_result_type": "no_new_resultant",
        "route": "STOP",
    }
    false_closed_stages = [
        generated_topology_stage02,
        synthetic_stage04(generated_topology_stage02["burden_floor"]),
        false_closed_generated_stage05,
        normalized_stage06,
    ]
    false_closed_mrp_text = stage07_mrp_reread_section_scaffold(false_closed_stages)
    false_closed_witness_text = stage07_field_witness_section_scaffold(false_closed_stages)
    false_closed_payload = first_json_object_from_text(false_closed_witness_text)
    if false_closed_payload is None:
        raise HarnessError("Self-test generated false-closed canary did not emit field_witness JSON")
    if false_closed_payload.get("terminal_states", {}).get("B6") == "landed":
        raise HarnessError("Self-test generated false-closed canary left unexecuted B_MRP as landed")
    if false_closed_payload.get("coverage_proof", {}).get("coverage_complete") is not False:
        raise HarnessError("Self-test generated false-closed canary claimed coverage_complete=true")
    if "HOLD(⁶B)" not in false_closed_mrp_text or "coverage_complete=false" not in false_closed_mrp_text:
        raise HarnessError("Self-test generated false-closed canary did not render public HOLD/PARTIAL accounting")
    false_closed_states = false_closed_payload.get("formal_reread_states", [])
    if not any(
        isinstance(row, dict)
        and row.get("source_burden") == "B6"
        and row.get("route_result_type") == "hold_partial"
        and row.get("route") == "HOLD"
        for row in false_closed_states
    ):
        raise HarnessError("Self-test generated false-closed canary did not normalize terminal STOP to HOLD")
    drifted_mrp_text = (
        "[Mid-Reread Pressure]\n"
        "Target: MRP(¹B)\n"
        "R(H,Δ): old model prose only.\n"
        "MRP route result type: generated_burden_instantiation\n"
        "MRP resultant: model drift without generated heading\n"
        "Route: RECURSE\n"
    )
    canonical_mrp_text, canonical_mrp_event = canonical_compiled_structural_section(
        "mrp_reread_terminal",
        drifted_mrp_text,
        [wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
    )
    if not canonical_mrp_event:
        raise HarnessError("Self-test Stage 07 structural MRP canonicalization did not record an event")
    for required in (
        "MRP terminal reconstruction floor:",
        "- MRP(⁵B): type=generated_burden_instantiation; finding=genuine-dependent; graph=⁵B → ⁶B; route=RECURSE",
        "## Burden 6 / ⁶B [generated-by: MRP(⁵B)]",
        "HOLD(⁶B): generated MRP burden remains unresolved/unexecuted",
        "- MRP(⁶B): type=hold_partial; finding=partial-real; graph=none; route=HOLD",
        "⁶B: carried-RECURSE",
    ):
        if required not in canonical_mrp_text:
            raise HarnessError(f"Self-test Stage 07 structural MRP canonicalization omitted scaffold: {required}")
    if "old model prose only" in canonical_mrp_text:
        raise HarnessError("Self-test Stage 07 structural MRP canonicalization retained drifted model MRP prose")
    if "[Mid-Reread Pressure]" in canonical_mrp_text:
        raise HarnessError("Self-test Stage 07 structural MRP canonicalization must replace heading blocks with the ledger-only section")

    drifted_field_witness = (
        "Closure/Reconstruction Witness\n"
        "field_witness\n"
        "{\n"
        '  "B_LA": ["B1", "B2", "B3", "B4", "B5"],\n'
        '  "B_MRP": ["B6"],\n'
        '  "B_total": ["B1", "B2", "B3", "B4", "B5", "B6"],\n'
        '  "generated_burdens": [{"id": "B6", "generated_by": "MRP(B5)"}],\n'
        '  "mrp_resultants": [{"source": "B5", "type": "generated_burden_instantiation", "graph": "B5 -> B6", "route": "RECURSE"}],\n'
        '  "formal_reread_states": [{"source_burden": "B5", "curl_state": null}],\n'
        '  "coverage_proof": {"coverage_complete": true, "diagnostic_completeness": {"coverage": {"xi": ["B6"]}}}\n'
        "}\n"
    )
    canonical_witness_text, canonical_witness_event = canonical_compiled_structural_section(
        "field_witness_nar",
        drifted_field_witness,
        [wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
    )
    if not canonical_witness_event:
        raise HarnessError("Self-test Stage 07 structural field_witness canonicalization did not record an event")
    for required in (
        '"B_MRP": [\n    "B6"\n  ]',
        '"generated_by": "MRP(B5)"',
        '"source_burden": "B6"',
        '"route_result_type": "hold_partial"',
        '"divergence_state": "non-neutral"',
        '"curl_state": "held"',
        '"coverage_complete": false',
        '"owner_route": [\n        "source-status-repair.source-order",\n        "P7.scope-boundary"\n      ]',
    ):
        if required not in canonical_witness_text:
            raise HarnessError(f"Self-test Stage 07 structural field_witness canonicalization omitted scaffold: {required}")
    if '"coverage_complete": true' in canonical_witness_text or '"curl_state": null' in canonical_witness_text:
        raise HarnessError("Self-test Stage 07 structural field_witness canonicalization retained drifted proof values")
    public_alias_probe = (
        "This definition-anchored state is the final local repair for B2.\n"
        "B2_1[M7] repairs the local definition.\n"
        "Land(B2): local scope repaired.\n"
        "R(H,Delta): release B2.\n"
        "⟦ACT B2_1[M7.definition-anchor] :: π=definition :: body_ref=B2_1 :: Δ=ΔB2:definition-anchored :: Land(B2)+⟧\n"
        "field_witness\n"
        '{\n  "B_total": ["B2"],\n  "body_ref": "B2_1"\n}\n'
        "```\nB2 remains literal inside code fence\n```\n"
    )
    canonical_alias_text, canonical_alias_event = canonical_compiled_structural_section(
        "closing_formulation",
        public_alias_probe,
        [wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
    )
    if not canonical_alias_event or not canonical_alias_event.get("canonicalized_public_burden_aliases"):
        raise HarnessError("Self-test Stage 07 public burden alias canonicalization did not record an event")
    for required in (
        "final local repair for ²B",
        "²B₁[M7] repairs the local definition",
        "Land(²B): local scope repaired",
        "R(H,Δ): release ²B",
    ):
        if required not in canonical_alias_text:
            raise HarnessError(f"Self-test Stage 07 public burden alias canonicalization omitted {required}")
    for preserved in (
        "body_ref=B2_1",
        '"B_total": ["B2"]',
        '"body_ref": "B2_1"',
        "B2 remains literal inside code fence",
    ):
        if preserved not in canonical_alias_text:
            raise HarnessError(f"Self-test Stage 07 public burden alias canonicalization mutated machine/code text: {preserved}")
    generated_stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-generated-burden",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, generated_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Target: ¹B / bounded self-test burden",
        "R(H,Δ): held routes rechecked: ²B; live remainder: ²B; release/next: RECURSE to ²B.",
        "Landed delta: Δ¹B / Delta(B1): bounded-self-test-delta recorded.",
        "Route-gradient: newly generated ²B [generated-by: MRP(¹B)] is absent from B_LA after Δ ¹B post-Land field-pressure.",
        "Matched owner/TTP route: [source-status-repair.source-order], [P7.scope-boundary]",
        "Finding: genuine-dependent",
        "MRP route result type: generated_burden_instantiation",
        "MRP resultant: genuine-dependent -> graph ¹B → ²B; RECURSE",
        "Graph delta: ¹B → ²B",
        "Pre-emption basis: graph-bound",
        "Route: RECURSE",
        "MRP route result type: hold_partial",
        "Route: HOLD",
        "- MRP(¹B): type=generated_burden_instantiation; finding=genuine-dependent; graph=¹B → ²B; route=RECURSE",
        "- MRP(²B): type=hold_partial; finding=partial-real; graph=none; route=HOLD",
        "must mirror the Stage 05 per_burden_reread records 1:1",
    ):
        if required not in generated_stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 generated MRP prompt omitted scaffold: {required}")
    mapped_nar_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": {
                "n_frame": "science-only-source-order-warrant",
                "live_registers": ["xi", "kappa"],
                "burden_floor": ["B1"],
                "per_burden": {
                    "B1": {
                        "owner_id": "source-status-repair",
                        "operation": "source-order-repair",
                        "delta_result": "source-order-repaired",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    }
                },
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    mapped_rows = mapped_nar_stage06["normalized_activation_record"].get("per_burden")
    if not isinstance(mapped_rows, list) or mapped_rows[0].get("burden_id") != "B1":
        raise HarnessError("Self-test failed to normalize Stage 06 NAR per_burden map into object list")
    selected_detail_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": {
                "n_frame": {
                    "selected": "science-only-source-order-warrant",
                    "held": ["revelation-private-preference-frame"],
                },
                "live_registers": ["xi", "kappa"],
                "burden_floor": ["B1"],
                "per_burden": [
                    {
                        "burden_id": "B1",
                        "owner_id": "source-status-repair",
                        "operation": "source-order-repair",
                        "delta_result": "source-order-repaired",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    }
                ],
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    selected_detail_nar = selected_detail_stage06["normalized_activation_record"]
    if selected_detail_nar.get("n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to normalize object-shaped Stage 06 n_frame to selected scalar")
    selected_detail = selected_detail_nar.get("n_frame_details")
    if not isinstance(selected_detail, dict) or selected_detail.get("selected") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to preserve object-shaped Stage 06 n_frame under n_frame_details")
    selected_detail_normalization = selected_detail_nar.get("normalization")
    if not isinstance(selected_detail_normalization, dict) or selected_detail_normalization.get("n_frame_from_selected_detail") is not True:
        raise HarnessError("Self-test failed to record Stage 06 n_frame selected/detail normalization")
    supplemental_details_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": copy.deepcopy(structured_nar),
            "normalized_activation_record_details": {
                "n_frame_details": {
                    "selected": "science-only-source-order-warrant",
                    "held": ["revelation-private-preference-frame"],
                    "held_details": [
                        {
                            "n_frame": "revelation-private-preference-frame",
                            "hold_reason": "bounded self-test frame held rather than selected",
                        }
                    ],
                },
                "per_burden_count": 1,
                "generated_terminal_burdens_without_act": [],
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    supplemental_details = supplemental_details_stage06["normalized_activation_record_details"]
    if supplemental_details.get("n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to hydrate supplemental Stage 06 NAR details from canonical NAR")
    supplemental_normalization = supplemental_details.get("normalization")
    if not isinstance(supplemental_normalization, dict) or "per_burden" not in supplemental_normalization.get(
        "hydrated_from_normalized_activation_record", []
    ):
        raise HarnessError("Self-test failed to record supplemental Stage 06 NAR details hydration")
    supplemental_frame_details = supplemental_details.get("n_frame_details")
    if not isinstance(supplemental_frame_details, dict) or supplemental_frame_details.get("held") != [
        "revelation-private-preference-frame"
    ]:
        raise HarnessError("Self-test failed to preserve Stage 06 held n_frame string list")
    supplemental_held_details = supplemental_frame_details.get("held_details")
    if (
        not isinstance(supplemental_held_details, list)
        or not supplemental_held_details
        or supplemental_held_details[0].get("n_frame") != "revelation-private-preference-frame"
    ):
        raise HarnessError("Self-test failed to preserve Stage 06 held_details object list")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": copy.deepcopy(structured_nar),
                "normalized_activation_record_details": {
                    "n_frame_details": {
                        "selected": "science-only-source-order-warrant",
                        "held": [
                            {
                                "n_frame": "revelation-private-preference-frame",
                                "hold_reason": "object shape belongs in held_details, not held",
                            }
                        ],
                    },
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 06 n_frame_details.held object list")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": copy.deepcopy(structured_nar),
                "normalized_activation_record_details": {
                    "n_frame_details": {
                        "selected": "science-only-source-order-warrant",
                        "held": ["revelation-private-preference-frame"],
                        "held_details": [
                            {
                                "n_frame": "unlisted-held-frame",
                                "hold_reason": "detail must reference a held frame token",
                            }
                        ],
                    },
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 06 held_details outside held frame list")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": copy.deepcopy(structured_nar),
                "normalized_activation_record_details": {
                    "n_frame_details": {"selected": "mismatched-frame"},
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject supplemental Stage 06 NAR details with mismatched n_frame")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": True,
                "normalized_activation_record_details": {
                    "n_frame_details": {"selected": "science-only-source-order-warrant"},
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject supplemental Stage 06 NAR details without structured canonical NAR")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": {
                    "n_frame": {"held": ["revelation-private-preference-frame"]},
                    "live_registers": ["xi", "kappa"],
                    "burden_floor": ["B1"],
                    "per_burden": [{"burden_id": "B1"}],
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject object-shaped Stage 06 n_frame without selected scalar")
    stage06_local_record = base_record(
        "self-test-a9-science-source-stage06",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-06-field-witness-nar",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage06",
            replay_record,
            stop_after_stage="stage-06-field-witness-nar",
        ),
    )
    stage06_local_record["stages"] = [*replay["stages"][:5], normalized_stage06]
    stage06_local_path = run_dir / "staged-handoff-stage06-model-scope-record.json"
    write_json(stage06_local_path, stage06_local_record)
    validate_replay_record(root, stage06_local_path)

    stage06_nested_only_record = dict(stage06_local_record)
    stage06_nested_only_record["case_id"] = "self-test-stage06-register-deltas-nested-only"
    stage06_nested_only_record["model_scope"] = model_scope(
        "self-test-stage06-register-deltas-nested-only",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_nested_only_record["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_nested_only_record["stages"][-1] = dict(stage06_nested_only_record["stages"][-1])
    stage06_nested_nar = dict(stage06_nested_only_record["stages"][-1]["normalized_activation_record"])
    stage06_nested_nar["register_deltas"] = {"xi": "source-order-repaired"}
    stage06_nested_only_record["stages"][-1]["normalized_activation_record"] = stage06_nested_nar
    stage06_nested_only_record["stages"][-1].pop("register_deltas", None)
    stage06_nested_only_path = run_dir / "stage06-register-deltas-nested-only.invalid.json"
    write_json(stage06_nested_only_path, stage06_nested_only_record)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_nested_only_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 06 register_deltas nested only under NAR")

    stage06_register_delta_list_record = dict(stage06_local_record)
    stage06_register_delta_list_record["case_id"] = "self-test-stage06-register-delta-list-values"
    stage06_register_delta_list_record["model_scope"] = model_scope(
        "self-test-stage06-register-delta-list-values",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_register_delta_list_record["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_register_delta_list_record["stages"][-1] = dict(stage06_register_delta_list_record["stages"][-1])
    stage06_register_delta_list_record["stages"][-1]["register_deltas"] = [
        {"register": "Omega", "delta": ["B1:model-family-bounded", "B1:predicate-separated"]},
        {"register": "xi", "delta": "B1:source-order-landed"},
    ]
    stage06_register_delta_list_path = run_dir / "stage06-register-delta-list-values.valid.json"
    write_json(stage06_register_delta_list_path, stage06_register_delta_list_record)
    validate_replay_record(root, stage06_register_delta_list_path)

    for invalid_delta, suffix in [
        ([], "empty"),
        (["B1:source-order-landed", 1], "non-string-member"),
    ]:
        invalid_register_delta_record = dict(stage06_register_delta_list_record)
        invalid_register_delta_record["case_id"] = f"self-test-stage06-register-delta-list-{suffix}"
        invalid_register_delta_record["model_scope"] = model_scope(
            f"self-test-stage06-register-delta-list-{suffix}",
            replay_record,
            stop_after_stage="stage-06-field-witness-nar",
        )
        invalid_register_delta_record["stages"] = [
            dict(stage) for stage in stage06_register_delta_list_record["stages"]
        ]
        invalid_register_delta_record["stages"][-1] = dict(invalid_register_delta_record["stages"][-1])
        invalid_register_delta_record["stages"][-1]["register_deltas"] = [
            {"register": "xi", "delta": invalid_delta}
        ]
        invalid_register_delta_path = run_dir / f"stage06-register-delta-list-{suffix}.invalid.json"
        write_json(invalid_register_delta_path, invalid_register_delta_record)
        invalid_result = run_checked(
            [
                sys.executable,
                str(root / "tools" / "check_staged_runtime_handshake.py"),
                "--records",
                str(invalid_register_delta_path),
            ],
            cwd=root,
        )
        if invalid_result.returncode == 0:
            raise HarnessError(
                f"Self-test failed to reject Stage 06 register_deltas list-object {suffix} delta"
            )

    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": [{"burden_id": "B1"}],
                "normalized_activation_record": structured_nar,
                "register_deltas": {},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 06 owner_activation object without body_ref")

    stage06_boolean_nar = dict(stage06_local_record)
    stage06_boolean_nar["case_id"] = "self-test-stage06-boolean-nar-no-details"
    stage06_boolean_nar["model_scope"] = model_scope(
        "self-test-stage06-boolean-nar-no-details",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_boolean_nar["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_boolean_nar["stages"][-1] = dict(stage06_boolean_nar["stages"][-1])
    stage06_boolean_nar["stages"][-1].pop("normalized_activation_record_details", None)
    stage06_boolean_nar["stages"][-1]["normalized_activation_record"] = True
    stage06_boolean_nar_path = run_dir / "stage06-boolean-nar-no-details.invalid.json"
    write_json(stage06_boolean_nar_path, stage06_boolean_nar)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_boolean_nar_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 06 boolean NAR without details")

    stage06_floor_mismatch = dict(stage06_local_record)
    stage06_floor_mismatch["case_id"] = "self-test-stage06-nar-floor-mismatch"
    stage06_floor_mismatch["model_scope"] = model_scope(
        "self-test-stage06-nar-floor-mismatch",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_floor_mismatch["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_floor_mismatch["stages"][-1] = dict(stage06_floor_mismatch["stages"][-1])
    stage06_floor_mismatch["stages"][-1]["normalized_activation_record"] = dict(structured_nar)
    stage06_floor_mismatch["stages"][-1]["normalized_activation_record"]["burden_floor"] = ["B999"]
    stage06_floor_mismatch_path = run_dir / "stage06-nar-floor-mismatch.invalid.json"
    write_json(stage06_floor_mismatch_path, stage06_floor_mismatch)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_floor_mismatch_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 06 NAR burden_floor mismatch")

    stage06_release_output = dict(stage06_local_record)
    stage06_release_output["case_id"] = "self-test-stage06-release-output"
    stage06_release_output["model_scope"] = model_scope(
        "self-test-stage06-release-output",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_release_output["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_release_output["stages"][-1] = dict(stage06_release_output["stages"][-1])
    stage06_release_output["stages"][-1]["release_output"] = {"path": "output.md"}
    stage06_release_output_path = run_dir / "stage06-release-output.invalid.json"
    write_json(stage06_release_output_path, stage06_release_output)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_release_output_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 06 release_output")

    stage07_validation = {
        "visible_opening_header": "pass",
        "nla_semantic_faithfulness": "pass",
        "field_witness_convergence": "pass",
        "formal_reread_state_semantics": "pass",
        "mid_reread_pressure": "pass",
        "mrp_record_surface_parity": "pass",
        "mrp_generated_burden": "pass",
        "graph_completeness_json": "pass",
        "manual_smoke_render_contract": "pass",
        "public_burden_grouping": "pass",
        "owner_activation_ordering": "pass",
    }
    if STAGE07_RELEASE_VALIDATION_ORDER.index("mrp_generated_burden") > STAGE07_RELEASE_VALIDATION_ORDER.index(
        "graph_completeness_json"
    ):
        raise HarnessError("Self-test Stage 07 validator order must run MRP before graph completeness")
    replay_stage07 = stage_by_id(replay.get("stages", []), "stage-07-release-output") or {}
    replay_release_output = replay_stage07.get("release_output") if isinstance(replay_stage07, dict) else {}
    if not isinstance(replay_release_output, dict) or not isinstance(replay_release_output.get("path"), str):
        raise HarnessError("Self-test replay record missing Stage 07 release_output.path")
    replay_output_path = resolve_under_root(root, replay_release_output["path"], "self-test Stage 07 release output")
    stage07_diagnostics = build_release_field_diagnostics(replay_output_path)
    if stage07_diagnostics.get("matches") is not True:
        raise HarnessError("Self-test replay output did not produce matching release_field_diagnostics")

    visible_probe_witness = {
        "B_LA": ["B1"],
        "B_MRP": [],
        "B_total": ["B1"],
        "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
        "terminal_states": {"B1": "landed"},
        "owner_activations": [
            {
                "body_ref": "B1_1",
                "target": "B1",
                "owner": "M7",
                "owner_id": "M7",
                "operation": "definition-anchor",
                "pressure": "definition-pressure",
                "delta": "DeltaB1:definition-anchored",
                "delta_result": "definition-anchored",
                "land": "Land(B1)",
                "land_target": "B1",
            }
        ],
        "normalized_activation_record": {
            "n_frame": "neutral-visible-projection",
            "live_registers": ["mu"],
            "burden_floor": ["B1"],
            "per_burden": [
                {
                    "burden_id": "B1",
                    "owner_id": "M7",
                    "operation": "definition-anchor",
                    "delta_result": "definition-anchored",
                    "terminal_state": "landed",
                    "generation_depth": 0,
                }
            ],
        },
        "coverage_proof": {
            "initial_burden_set": ["B1"],
            "terminal_states": {"B1": "landed"},
            "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": True},
            "divergence_check": "neutral",
            "curl_check": "null",
            "coverage_complete": True,
        },
    }
    visible_probe_base = "\n".join(
        [
            "NOETIC FIELD EXECUTION",
            "Layer A / Diagnostic IR Header",
            "Layer B / Burden 1",
            "⟦ACT B1_1[M7.definition-anchor] :: π=definition-pressure :: body_ref=B1_1 :: Δ=ΔB1:definition-anchored :: Land(B1)+⟧",
            "MRP(B1): type=no_new_resultant; graph=none; route=STOP",
            "Restorative Response",
            "Closing Formulation",
            "Closure/Reconstruction Witness",
            "Terminal states:",
            "B1: landed / ACT owners / landed by visible owner activations",
            "field_witness",
            json.dumps(visible_probe_witness, ensure_ascii=False, indent=2),
            "",
        ]
    )
    visible_probe_path = run_dir / "stage07-visible-output-valid-probe.md"
    visible_probe_path.write_text(visible_probe_base, encoding="utf-8")
    visible_probe_errors = visible_governed_output_errors(visible_probe_path)
    if visible_probe_errors:
        raise HarnessError(
            "Self-test Stage 07 visible-output valid probe failed: " + ", ".join(visible_probe_errors)
        )

    def assert_visible_output_rejects(name: str, text: str, expected: str) -> None:
        probe_path = run_dir / f"{name}.invalid.md"
        probe_path.write_text(text, encoding="utf-8")
        found = visible_governed_output_errors(probe_path)
        if expected not in found:
            raise HarnessError(
                f"Self-test Stage 07 visible-output probe {name} missed {expected!r}; found: {found}"
            )

    assert_visible_output_rejects(
        "stage07-field-witness-heading-only",
        visible_probe_base.rsplit("\nfield_witness\n", 1)[0] + "\nfield_witness\nB_LA: B1\n",
        "parser-stable field_witness object",
    )
    no_nar_witness = dict(visible_probe_witness)
    no_nar_witness.pop("normalized_activation_record", None)
    assert_visible_output_rejects(
        "stage07-field-witness-missing-nar",
        visible_probe_base.rsplit("\nfield_witness\n", 1)[0]
        + "\nfield_witness\n"
        + json.dumps(no_nar_witness, ensure_ascii=False, indent=2)
        + "\n",
        "normalized_activation_record / NAR evidence",
    )
    assert_visible_output_rejects(
        "stage07-guaranteed-tlang-proof-claim",
        visible_probe_base + "\nT_lang guarantees interlocutor uptake.\n",
        "guaranteed T_lang uptake claim",
    )
    assert_visible_output_rejects(
        "stage07-activegraph-proof-claim",
        visible_probe_base + "\nActiveGraph proof confirms retained closure.\n",
        "Graphify/ActiveGraph proof claim",
    )
    assert_visible_output_rejects(
        "stage07-duplicate-restorative-response",
        visible_probe_base.replace(
            "Closing Formulation\n",
            "Restorative Response\nDuplicated public tail.\nClosing Formulation\n",
            1,
        ),
        "visible output: duplicate singleton final public heading 'Restorative Response'",
    )
    assert_visible_output_rejects(
        "stage07-closure-witness-before-closing",
        visible_probe_base.replace(
            "Closing Formulation\n",
            "Closure/Reconstruction Witness\nPremature proof tail.\nClosing Formulation\n",
            1,
        ),
        "visible output: duplicate singleton final public heading 'Closure/Reconstruction Witness'",
    )

    stage07_local_record = base_record(
        "self-test-a9-science-source-stage07",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-07-release-output",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage07",
            replay_record,
            stop_after_stage="stage-07-release-output",
        ),
    )
    stage07_stage = dict(replay["stages"][6])
    stage07_stage["release_validation"] = dict(stage07_validation)
    stage07_stage["release_field_diagnostics"] = dict(stage07_diagnostics)
    stage07_local_record["stages"] = [*replay["stages"][:6], stage07_stage]
    if stage07_local_record.get("stage_scope", {}).get("release_output") is not True:
        raise HarnessError("Self-test failed to mark Stage 07 scope as release-output producing")
    if stage07_local_record.get("stage_scope", {}).get("not_release_output") is True:
        raise HarnessError("Self-test Stage 07 scope must not carry not_release_output=true")
    stage07_local_path = run_dir / "staged-handoff-stage07-model-scope-record.json"
    write_json(stage07_local_path, stage07_local_record)
    validate_replay_record(root, stage07_local_path)
    run_compiled_release_self_test(
        root=root,
        run_dir=run_dir,
        replay_output_path=replay_output_path,
        replay_record=replay_record,
        replay=replay,
        stage07_validation=stage07_validation,
    )

    stage07_missing_validation = dict(stage07_local_record)
    stage07_missing_validation["case_id"] = "self-test-stage07-missing-validation"
    stage07_missing_validation["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_missing_validation["stages"][-1] = dict(stage07_missing_validation["stages"][-1])
    stage07_missing_validation["stages"][-1].pop("release_validation", None)
    stage07_missing_validation_path = run_dir / "stage07-missing-release-validation.invalid.json"
    write_json(stage07_missing_validation_path, stage07_missing_validation)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_missing_validation_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 07 missing release_validation")

    stage07_missing_diagnostics = dict(stage07_local_record)
    stage07_missing_diagnostics["case_id"] = "self-test-stage07-missing-release-field-diagnostics"
    stage07_missing_diagnostics["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_missing_diagnostics["stages"][-1] = dict(stage07_missing_diagnostics["stages"][-1])
    stage07_missing_diagnostics["stages"][-1].pop("release_field_diagnostics", None)
    stage07_missing_diagnostics_path = run_dir / "stage07-missing-release-field-diagnostics.invalid.json"
    write_json(stage07_missing_diagnostics_path, stage07_missing_diagnostics)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_missing_diagnostics_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 07 missing release_field_diagnostics")

    stage07_mismatched_diagnostics = dict(stage07_local_record)
    stage07_mismatched_diagnostics["case_id"] = "self-test-stage07-mismatched-release-field-diagnostics"
    stage07_mismatched_diagnostics["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_mismatched_diagnostics["stages"][-1] = dict(stage07_mismatched_diagnostics["stages"][-1])
    mismatched_diagnostics = json.loads(json.dumps(stage07_diagnostics))
    mismatched_diagnostics["field_witness_coverage"]["divergence_check"] = "non-neutral"
    mismatched_diagnostics["matches"] = True
    stage07_mismatched_diagnostics["stages"][-1]["release_field_diagnostics"] = mismatched_diagnostics
    stage07_mismatched_diagnostics_path = run_dir / "stage07-mismatched-release-field-diagnostics.invalid.json"
    write_json(stage07_mismatched_diagnostics_path, stage07_mismatched_diagnostics)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_mismatched_diagnostics_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 mismatched release_field_diagnostics")

    stage07_failed_validation = dict(stage07_local_record)
    stage07_failed_validation["case_id"] = "self-test-stage07-failed-validation"
    stage07_failed_validation["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_failed_validation["stages"][-1] = dict(stage07_failed_validation["stages"][-1])
    stage07_failed_validation["stages"][-1]["release_validation"] = dict(stage07_validation)
    stage07_failed_validation["stages"][-1]["release_validation"]["nla_semantic_faithfulness"] = "fail"
    stage07_failed_validation_path = run_dir / "stage07-failed-release-validation.invalid.json"
    write_json(stage07_failed_validation_path, stage07_failed_validation)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_failed_validation_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 failed release_validation")

    stage07_with_sidecars = dict(stage07_local_record)
    stage07_with_sidecars["case_id"] = "self-test-stage07-with-sidecars"
    stage07_with_sidecars["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_with_sidecars["stages"][-1] = dict(stage07_with_sidecars["stages"][-1])
    stage07_with_sidecars["stages"][-1]["verifier_sidecars"] = {"claimed": True}
    stage07_with_sidecars_path = run_dir / "stage07-with-sidecars.invalid.json"
    write_json(stage07_with_sidecars_path, stage07_with_sidecars)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_with_sidecars_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 verifier_sidecars")
    print("staged current-skill harness self-test: PASS")
    print(f"self-test run dir: {rel(run_dir, root)}")
    print(f"handoff record: {rel(record_path, root)}")
    print(f"hashes: {rel(hash_path, root)}")
    return 0


def visible_governed_output_errors(output_path: Path) -> list[str]:
    text = output_path.read_text(encoding="utf-8", errors="replace")
    checks = [
        ("visible noetic-field opening/header", r"NOETIC FIELD EXECUTION|noetic-field"),
        ("compact Layer A / Diagnostic IR header", r"Layer A\b.*(DSL/IR|Diagnostic IR|Header)"),
        ("governed Layer B / burden execution surface", r"Layer B\b|Bounded Governed Response|Burden\s+\d+"),
        ("canonical ACT-readable rows", r"⟦ACT\b"),
        ("ACT body_ref tokens", r"\bbody_ref="),
        ("Land surface", r"Land\("),
        ("MRP / reread / terminal state surface", r"MRP\(|R\(H,|Mid-Reread|Terminal states"),
        ("field_witness heading", r"(?m)^\s*field_witness\b"),
        ("normalized_activation_record / NAR evidence", r"normalized_activation_record|\bNAR\b"),
        ("Restorative Response", r"(?im)^\s*(?:#+\s*)?Restorative Response\b"),
        ("Closing Formulation", r"(?im)^\s*(?:#+\s*)?Closing Formulation\b"),
    ]
    errors = [label for label, pattern in checks if re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is None]
    errors.extend(staged_output.final_public_tail_errors(text, "visible output"))
    witness_payload = extract_embedded_field_witness(text)
    field_witness = extract_field_witness(witness_payload)
    if re.search(r"(?m)^\s*field_witness\b", text, re.IGNORECASE | re.MULTILINE) and field_witness is None:
        errors.append("parser-stable field_witness object")
    if isinstance(field_witness, dict) and not isinstance(field_witness.get("normalized_activation_record"), dict):
        errors.append("normalized_activation_record / NAR evidence")
    forbidden = [
        ("harness commentary", r"You are executing stage-|Validated compact stage state|Return exactly one JSON object"),
        ("package/provenance claim", r"\bpackage/provenance\b|provenance asset|release package|\.skill\b|GitHub Release"),
        ("guaranteed T_lang uptake claim", r"T_lang guarantees|guaranteed T_lang uptake|guarantees interlocutor uptake"),
        ("Graphify/ActiveGraph proof claim", r"Graphify[^.\n]{0,80}\bproof\b|ActiveGraph[^.\n]{0,80}\bproof\b"),
    ]
    errors.extend(label for label, pattern in forbidden if re.search(pattern, text, re.IGNORECASE))
    return errors


def coverage_status(field_witness: dict[str, Any] | None, key: str) -> str:
    if not isinstance(field_witness, dict):
        return ""
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return ""
    value = coverage.get(key)
    if not isinstance(value, str):
        return ""
    return status_head(value)


def build_release_field_diagnostics(output_path: Path) -> dict[str, Any]:
    text = output_path.read_text(encoding="utf-8", errors="replace")
    witness = parse_closure_witness(text)
    field_witness = extract_field_witness(extract_embedded_field_witness(text))
    visible = {
        "divergence_check": status_head(witness.divergence) if witness is not None else "",
        "curl_check": status_head(witness.curl) if witness is not None else "",
    }
    field_witness_coverage = {
        "divergence_check": coverage_status(field_witness, "divergence_check"),
        "curl_check": coverage_status(field_witness, "curl_check"),
    }
    matches = (
        visible["divergence_check"] in RELEASE_DIVERGENCE_STATES
        and visible["curl_check"] in RELEASE_CURL_STATES
        and visible == field_witness_coverage
    )
    return {
        "visible": visible,
        "field_witness_coverage": field_witness_coverage,
        "matches": matches,
    }


def run_release_validators(
    root: Path,
    output_path: Path,
    per_burden_reread: list[dict[str, Any]],
) -> dict[str, str]:
    visible_errors = visible_governed_output_errors(output_path)
    if visible_errors:
        raise HarnessError(
            "stage-07-release-output: visible governed output validation failed:\n- "
            + "\n- ".join(visible_errors)
        )
    validators = [
        (
            "nla_semantic_faithfulness",
            [sys.executable, str(root / "tools" / "check_nla_decode_semantic_faithfulness.py"), "--outputs", str(output_path)],
        ),
        (
            "field_witness_convergence",
            [sys.executable, str(root / "tools" / "check_field_witness_convergence.py"), "--outputs", str(output_path)],
        ),
        (
            "formal_reread_state_semantics",
            [sys.executable, str(root / "tools" / "check_formal_reread_state_semantics.py"), "--outputs", str(output_path)],
        ),
        (
            "mid_reread_pressure",
            [sys.executable, str(root / "tools" / "check_mid_reread_pressure.py"), "--outputs", str(output_path)],
        ),
        (
            "mrp_generated_burden",
            [
                sys.executable,
                str(root / "tools" / "check_mrp_generated_burden.py"),
                "--outputs",
                str(output_path),
                "--show-advisories",
            ],
        ),
        (
            "graph_completeness_json",
            [sys.executable, str(root / "tools" / "check_graph_completeness.py"), "--outputs", str(output_path), "--json"],
        ),
        (
            "manual_smoke_render_contract",
            [sys.executable, str(root / "tools" / "check_manual_smoke_render_contract.py"), "--outputs", str(output_path)],
        ),
        (
            "public_burden_grouping",
            [sys.executable, str(root / "tools" / "check_public_burden_grouping.py"), "--outputs", str(output_path)],
        ),
        (
            "owner_activation_ordering",
            [sys.executable, str(root / "tools" / "check_owner_activation_ordering.py"), "--require-plan", "--outputs", str(output_path)],
        ),
    ]
    results = {"visible_opening_header": "pass"}
    for key, command in validators:
        require_command_success(command, cwd=root)
        results[key] = "pass"
        if key == "mid_reread_pressure":
            parity_errors = staged_output.visible_block_parity_errors(
                output_path.read_text(encoding="utf-8", errors="replace"),
                per_burden_reread,
            )
            if parity_errors:
                raise HarnessError(
                    "stage-07-release-output: MRP record-surface parity failed; visible "
                    "[Mid-Reread Pressure] blocks must mirror the stage-05 per_burden_reread "
                    "records verbatim:\n- " + "\n- ".join(parity_errors)
                )
            results["mrp_record_surface_parity"] = "pass"
    missing = STAGE07_RELEASE_VALIDATION_KEYS - set(results)
    if missing:
        raise HarnessError(f"stage-07-release-output: internal validator set missing {sorted(missing)}")
    return results


def build_sidecars(
    *,
    root: Path,
    raw_input: Path,
    output_path: Path,
    out_dir: Path,
    prefix: str,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_nla_decode_semantic_faithfulness.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_field_witness_convergence.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_formal_reread_state_semantics.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_graph_completeness.py"),
            "--outputs",
            str(output_path),
            "--json",
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "build_retained_proof_sidecars.py"),
            "--input",
            str(raw_input),
            "--output",
            str(output_path),
            "--out-dir",
            str(out_dir),
            "--prefix",
            prefix,
            "--force",
        ],
        cwd=root,
    )
    certificate = out_dir / f"{prefix}.collapse-certificate.json"
    grapher = out_dir / f"{prefix}.grapher.html"
    b5_sidecar = out_dir / f"{prefix}.b5-full-ir-projection-sidecar.json"
    eligibility_errors = b5_projection_eligibility_errors(load_json(certificate))
    if eligibility_errors:
        eligibility_path = out_dir / f"{prefix}.b5-full-ir-projection-eligibility.json"
        write_b5_projection_ineligibility(
            root=root,
            certificate_path=certificate,
            eligibility_path=eligibility_path,
            errors=eligibility_errors,
        )
        raise HarnessError(
            "stage-08-verifier-sidecars: B.5 full-IR projection ineligible: "
            + "; ".join(eligibility_errors)
            + f"; see {rel(eligibility_path, root)}"
        )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "build_b5_full_ir_projection_sidecar.py"),
            "--input",
            str(raw_input),
            "--output",
            str(output_path),
            "--collapse-certificate",
            str(certificate),
            "--grapher-html",
            str(grapher),
            "--out",
            str(b5_sidecar),
        ],
        cwd=root,
    )
    return [certificate, grapher, out_dir / f"{prefix}.hashes.json", b5_sidecar]


def materialize_smoke_raw_input(
    root: Path,
    run_dir: Path,
    raw_input_path: Path,
    raw_input_literal: str | None,
) -> Path:
    if raw_input_literal is not None:
        requested = raw_input_path if raw_input_path.is_absolute() else root / raw_input_path
        if requested.resolve() != DEFAULT_INPUT.resolve():
            raise HarnessError("--raw-input and --raw-input-path are mutually exclusive")
        run_dir.mkdir(parents=True, exist_ok=True)
        literal_path = run_dir / "raw-input.md"
        write_text(literal_path, str(raw_input_literal).rstrip() + "\n")
        return literal_path
    return resolve_under_root(root, raw_input_path, "Raw input")


def raw_input_preflight_payload(root: Path, raw_input_path: Path, raw_input_literal: str | None) -> dict[str, Any]:
    if raw_input_literal is not None:
        requested = raw_input_path if raw_input_path.is_absolute() else root / raw_input_path
        if requested.resolve() != DEFAULT_INPUT.resolve():
            raise HarnessError("--raw-input and --raw-input-path are mutually exclusive")
        literal_text = str(raw_input_literal).rstrip() + "\n"
        if not literal_text.strip():
            raise HarnessError("--raw-input must not be empty")
        return {
            "mode": "literal",
            "bytes": len(literal_text.encode("utf-8")),
            "sha256": hashlib.sha256(literal_text.encode("utf-8")).hexdigest().upper(),
        }
    resolved = resolve_under_root(root, raw_input_path, "Raw input")
    if not resolved.exists():
        raise HarnessError(f"Raw input does not exist: {rel(resolved, root)}")
    if not resolved.is_file():
        raise HarnessError(f"Raw input must be a file: {rel(resolved, root)}")
    text = resolved.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise HarnessError(f"Raw input must not be empty: {rel(resolved, root)}")
    return {
        "mode": "path",
        "path": rel(resolved, root),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def preflight_smoke_inputs(args: argparse.Namespace, root: Path, *, emit: bool = True) -> int:
    validate_required_files(root)
    if args.resume_run_dir is not None:
        raise HarnessError("--preflight-input-only validates fresh launches; do not combine it with --resume-run-dir")
    replay_record = resolve_under_root(root, args.replay_record, "Replay record")
    validate_replay_record(root, replay_record)
    run_dir = resolve_under_root(root, args.run_dir, "Run directory")
    if run_dir.exists():
        raise HarnessError(f"Run directory already exists: {rel(run_dir, root)}")
    raw_input_payload = raw_input_preflight_payload(root, args.raw_input_path, args.raw_input)
    if emit:
        print("staged current-skill input preflight: PASS")
        print(f"case name: {args.case_name}")
        print(f"run dir: {rel(run_dir, root)}")
        if raw_input_payload["mode"] == "path":
            print(f"raw input path: {raw_input_payload['path']}")
        else:
            print("raw input mode: literal")
        print(f"raw input bytes: {raw_input_payload['bytes']}")
        print(f"raw input sha256: {raw_input_payload['sha256']}")
        print(f"replay record: {rel(replay_record, root)}")
        print("non-claims: no model smoke; no staged response; no output.md; no sidecar; no retained promotion")
    return 0


def run_model_smoke(args: argparse.Namespace, root: Path) -> int:
    files = validate_required_files(root)
    run_dir = resolve_under_root(root, args.run_dir, "Run directory")
    resume_context: dict[str, Any] | None = None
    if args.resume_run_dir is not None:
        if args.raw_input is not None:
            raise HarnessError("--raw-input cannot be used with --resume-run-dir")
        resume_run_dir = resolve_under_root(root, args.resume_run_dir, "Resume run directory")
        if resume_run_dir != run_dir:
            raise HarnessError("--resume-run-dir and --run-dir must identify the same directory")
        resume_context = load_stage07_resume_context(root, resume_run_dir)
        replay_record = resume_context["replay_record_path"]
        raw_input = resume_context["raw_input_path"]
    else:
        replay_record = resolve_under_root(root, args.replay_record, "Replay record")
        raw_input = materialize_smoke_raw_input(root, run_dir, args.raw_input_path, args.raw_input)
    validate_replay_record(root, replay_record)
    run_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = run_dir / "prompts"
    responses_dir = run_dir / "responses"
    records_dir = run_dir / "records"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)
    records_dir.mkdir(parents=True, exist_ok=True)

    input_text = raw_input.read_text(encoding="utf-8", errors="replace")
    input_digest = sha256_file(raw_input)
    skill_hash = sha256_file(files["skill"])
    stages: list[dict[str, Any]] = list(resume_context["stages"]) if resume_context else []
    stage_files: list[Path] = list(resume_context["artifact_paths"]) if resume_context else []
    transport_attempts: list[dict[str, Any]] = list(resume_context["prior_attempts"]) if resume_context else []
    transport_attempts_record_path = records_dir / "stage-07-transport-attempts.json"
    if transport_attempts:
        write_transport_attempts_record(transport_attempts_record_path, root=root, attempts=transport_attempts)
        stage_files.append(transport_attempts_record_path)
    mode = "staged-current-skill-stage-local-smoke" if args.stop_after_stage else "staged-current-skill-smoke"
    release_output_mode = normalize_release_output_mode(args.release_output_mode)
    if resume_context is not None and release_output_mode != "compiled-output":
        raise HarnessError("--resume-run-dir requires --release-output-mode compiled")
    if resume_context is not None and args.stop_after_stage not in (None, "stage-07-release-output"):
        raise HarnessError("--resume-run-dir may only resume through stage-07-release-output or the full smoke")
    record = base_record(
        args.case_name,
        mode,
        not_model_smoke=False,
        stop_after_stage=args.stop_after_stage,
        model_scope_payload=model_scope(args.case_name, replay_record, stop_after_stage=args.stop_after_stage),
    )

    try:
        if resume_context is None:
            stage_ids_to_run = stage_order_for_stop(args.stop_after_stage)
            if args.stop_after_stage is None or args.stop_after_stage == "stage-07-release-output":
                stage_ids_to_run = STAGE_ORDER[:6]
            for stage_id in stage_ids_to_run:
                prompt = stage_prompt(
                    root=root,
                    stage_id=stage_id,
                    case_name=args.case_name,
                    raw_input_path=raw_input,
                    input_text=input_text,
                    input_digest=input_digest,
                    skill_hash=skill_hash,
                    previous_stages=stages,
                )
                prompt_path = prompts_dir / f"{stage_id}.prompt.md"
                response_path = responses_dir / f"{stage_id}.response.txt"
                log_path = responses_dir / f"{stage_id}.codex-log.txt"
                write_text(prompt_path, prompt)
                exit_code = invoke_codex(root, args.model, prompt, response_path, log_path)
                stage_files.extend([prompt_path, response_path, log_path])
                if exit_code != 0:
                    raise HarnessError(f"{stage_id}: codex exec failed with exit code {exit_code}; see {rel(log_path, root)}")
                payload = extract_json_object(response_path.read_text(encoding="utf-8", errors="replace"))
                stage = normalized_stage(stage_id, payload)
                if stage.get("status") == "fail":
                    raise HarnessError(f"{stage_id}: model returned fail: {stage.get('error')}")
                stages.append(stage)
                validate_incremental_handoffs(stages)
                write_json(records_dir / f"{stage_id}.stage.json", stage)
                if args.stop_after_stage == stage_id:
                    record["stages"] = stages
                    handoff_record = records_dir / "staged-handoff-stage-local-record.json"
                    write_json(handoff_record, record)
                    validate_replay_record(root, handoff_record)
                    hash_path = run_dir / "staged-smoke.hashes.json"
                    write_hash_record(
                        hash_path,
                        root=root,
                        case_name=args.case_name,
                        mode=mode,
                        model=args.model,
                        skill_path=files["skill"],
                        replay_record=replay_record,
                        raw_input_path=raw_input,
                        run_dir=run_dir,
                        stage_files=stage_files + [handoff_record],
                        handoff_record=handoff_record,
                        output_path=None,
                        sidecar_paths=[],
                        verdict=f"STAGED_CURRENT_SKILL_STAGE_LOCAL_PASS: stopped after {stage_id}",
                    )
                    print("staged current-skill stage-local smoke: PASS")
                    print(f"run dir: {rel(run_dir, root)}")
                    print(f"stop-after-stage: {stage_id}")
                    print(f"handoff record: {rel(handoff_record, root)}")
                    print(f"hashes: {rel(hash_path, root)}")
                    return 0

        output_path = run_dir / "output.md"
        assembly_record: dict[str, Any] | None = None
        if release_output_mode == "compiled-output":
            section_plan = compiled_release_section_plan(args.target_output_kb)
            section_budgets = compiled_section_budgets(section_plan, args.target_output_kb)
            min_section_bytes = (
                dict(section_budgets.get("min_section_bytes", {}))
                if isinstance(section_budgets, dict)
                else {}
            )
            act_partition = compiled_act_partition(stages, section_plan)
            assigned_refs_by_section = {
                str(item["section_id"]): list(item["body_refs"])
                for item in act_partition["assignments"]
                if isinstance(item, dict)
            }
            sections_dir = run_dir / "release-sections"
            sections_dir.mkdir(parents=True, exist_ok=True)
            expansions_dir = run_dir / "release-section-expansions"
            if args.section_expansion_rounds:
                expansions_dir.mkdir(parents=True, exist_ok=True)
            section_entries: list[dict[str, str]] = []
            expansion_records: list[dict[str, Any]] = (
                existing_expansion_records_for_resume(
                    root=root,
                    run_dir=run_dir,
                    section_plan=section_plan,
                    max_rounds=args.section_expansion_rounds,
                    artifact_hashes=resume_context["artifact_hashes"],
                )
                if resume_context is not None
                else []
            )
            expansion_record_paths = {str(Path(record["path"]).resolve()) for record in expansion_records}
            if args.section_expansion_rounds:
                stage_files.append(transport_attempts_record_path)
            for index, (section_id, section_role) in enumerate(section_plan, start=1):
                section_min_bytes = int(min_section_bytes.get(section_id, 0) or 0)
                assigned_refs = assigned_refs_by_section.get(section_id)
                section_prompt = release_section_prompt(
                    root=root,
                    case_name=args.case_name,
                    raw_input_path=raw_input,
                    input_text=input_text,
                    input_digest=input_digest,
                    skill_hash=skill_hash,
                    previous_stages=stages,
                    section_id=section_id,
                    section_role=section_role,
                    section_number=index,
                    section_count=len(section_plan),
                    target_output_kb=args.target_output_kb,
                    section_min_bytes=section_min_bytes,
                    assigned_body_refs=assigned_refs,
                )
                safe_section_id = section_id.replace("_", "-")
                section_prompt_path = prompts_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.prompt.md"
                section_output_path = sections_dir / f"{index:02d}-{safe_section_id}.md"
                section_log_path = responses_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.codex-log.txt"
                if resume_context is not None and section_output_path.exists():
                    require_hash_matched(
                        section_output_path,
                        root=root,
                        artifact_hashes=resume_context["artifact_hashes"],
                        label="resumed section output",
                    )
                else:
                    write_text(section_prompt_path, section_prompt)
                    exit_code = invoke_codex(root, args.model, section_prompt, section_output_path, section_log_path)
                    stage_files.extend([section_prompt_path, section_output_path, section_log_path])
                    if exit_code != 0:
                        raise HarnessError(
                            f"stage-07-release-output {section_id}: codex exec failed with exit code {exit_code}; "
                            f"see {rel(section_log_path, root)}"
                        )
                    if not section_output_path.exists() or section_output_path.stat().st_size == 0:
                        raise HarnessError(f"stage-07-release-output {section_id}: section output was not produced")
                for expansion_round in range(1, args.section_expansion_rounds + 1):
                    current_text = section_output_path.read_text(encoding="utf-8", errors="replace")
                    current_bytes = len(current_text.encode("utf-8"))
                    if not section_min_bytes or current_bytes >= section_min_bytes:
                        break
                    expansion_prompt = release_section_expansion_prompt(
                        root=root,
                        case_name=args.case_name,
                        raw_input_path=raw_input,
                        input_digest=input_digest,
                        skill_hash=skill_hash,
                        section_id=section_id,
                        section_role=section_role,
                        section_min_bytes=section_min_bytes,
                        current_bytes=current_bytes,
                        expansion_round=expansion_round,
                        max_rounds=args.section_expansion_rounds,
                        assigned_body_refs=assigned_refs,
                        existing_text=current_text,
                    )
                    expansion_prompt_path = (
                        prompts_dir
                        / f"stage-07-release-output-{index:02d}-{safe_section_id}-expansion-{expansion_round}.prompt.md"
                    )
                    expansion_output_path = (
                        expansions_dir / f"{index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
                    )
                    expansion_log_path = (
                        responses_dir
                        / f"stage-07-release-output-{index:02d}-{safe_section_id}-expansion-{expansion_round}.codex-log.txt"
                    )
                    if resume_context is not None and expansion_output_path.exists():
                        require_hash_matched(
                            expansion_output_path,
                            root=root,
                            artifact_hashes=resume_context["artifact_hashes"],
                            label="resumed expansion output",
                        )
                    else:
                        failed_expansion = resume_context.get("failed_expansion") if resume_context else None
                        is_resumed_failed_expansion = (
                            isinstance(failed_expansion, dict)
                            and failed_expansion.get("section_id") == section_id
                            and failed_expansion.get("round") == expansion_round
                        )
                        first_attempt = 2 if is_resumed_failed_expansion else 1
                        expansion_output_path = invoke_expansion_with_transport_policy(
                            root=root,
                            model=args.model,
                            prompt=expansion_prompt,
                            base_prompt_path=expansion_prompt_path,
                            base_output_path=expansion_output_path,
                            base_log_path=expansion_log_path,
                            section_id=section_id,
                            section_role=section_role,
                            expansion_round=expansion_round,
                            first_attempt=first_attempt,
                            retry_rounds=args.transport_retry_rounds,
                            attempts=transport_attempts,
                            attempts_record_path=transport_attempts_record_path,
                            stage_files=stage_files,
                        )
                    if not expansion_output_path.exists() or expansion_output_path.stat().st_size == 0:
                        raise HarnessError(
                            f"stage-07-release-output {section_id} expansion {expansion_round}: "
                            "expansion output was not produced"
                        )
                    expansion_text = expansion_output_path.read_text(encoding="utf-8", errors="replace").strip()
                    if not expansion_text:
                        raise HarnessError(
                            f"stage-07-release-output {section_id} expansion {expansion_round}: "
                            "expansion output was empty"
                        )
                    if str(expansion_output_path.resolve()) not in expansion_record_paths:
                        separator = "\n" if current_text.endswith("\n") else "\n\n"
                        write_text(section_output_path, current_text + separator + expansion_text + "\n")
                        expansion_records.append(
                            {
                                "section_id": section_id,
                                "role": section_role,
                                "round": expansion_round,
                                "path": str(expansion_output_path),
                                "sha256": sha256_file(expansion_output_path),
                            }
                        )
                        expansion_record_paths.add(str(expansion_output_path.resolve()))
                current_text = section_output_path.read_text(encoding="utf-8", errors="replace")
                canonical_text, canonical_event = canonical_compiled_structural_section(
                    section_role,
                    current_text,
                    stages,
                )
                if canonical_event is not None:
                    write_text(section_output_path, canonical_text)
                    current_text = canonical_text
                budget_text, budget_event = compiled_section_budget_guardrail(
                    section_role,
                    current_text,
                    stages,
                    section_min_bytes,
                )
                if budget_event is not None:
                    write_text(section_output_path, budget_text)
                section_entries.append(
                    {
                        "id": section_id,
                        "role": section_role,
                        "path": str(section_output_path),
                        "sha256": sha256_file(section_output_path),
                    }
                )
            assembly_manifest_path = run_dir / "stage-07-output-assembly.manifest.json"
            transport_resume_payload = None
            if resume_context is not None:
                transport_resume_payload = {
                    "schema": TRANSPORT_RESUME_SCHEMA,
                    "resumed": True,
                    "source_run_dir": resume_context["run_dir"],
                    "hash_record": resume_context["hash_record"],
                    "failure_record": resume_context["failure_record"],
                    "failed_expansion": resume_context["failed_expansion"],
                    "attempts_record": rel(transport_attempts_record_path, assembly_manifest_path.parent),
                    "attempts": transport_attempts,
                }
            write_compiled_release_manifest(
                root=root,
                manifest_path=assembly_manifest_path,
                case_name=args.case_name,
                raw_input_path=raw_input,
                section_entries=section_entries,
                output_path=output_path,
                per_burden_reread=stage05_per_burden_entries(
                    stage_by_id(stages, "stage-05-mrp-reread-terminal-state")
                ),
                target_output_kb=args.target_output_kb,
                act_partition=act_partition,
                section_budgets=section_budgets,
                section_expansions={
                    "schema": staged_output.SECTION_EXPANSIONS_SCHEMA,
                    "rounds_allowed": int(args.section_expansion_rounds or 0),
                    "records": [
                        {
                            "section_id": record["section_id"],
                            "role": record["role"],
                            "round": record["round"],
                            "path": rel(Path(record["path"]), assembly_manifest_path.parent),
                            "sha256": record["sha256"],
                        }
                        for record in expansion_records
                    ],
                }
                if args.section_expansion_rounds or expansion_records
                else None,
                transport_resume=transport_resume_payload,
            )
            stage_files.append(assembly_manifest_path)
            assembly_record = assemble_compiled_manifest(assembly_manifest_path, root=root)
            assembly_hash_path = output_path.with_suffix(output_path.suffix + ".assembly.hashes.json")
            if assembly_hash_path.exists():
                stage_files.append(assembly_hash_path)
        else:
            release = release_prompt(
                root=root,
                case_name=args.case_name,
                raw_input_path=raw_input,
                input_text=input_text,
                input_digest=input_digest,
                skill_hash=skill_hash,
                previous_stages=stages,
            )
            release_prompt_path = prompts_dir / "stage-07-release-output.prompt.md"
            release_log_path = responses_dir / "stage-07-release-output.codex-log.txt"
            write_text(release_prompt_path, release)
            exit_code = invoke_codex(root, args.model, release, output_path, release_log_path)
            stage_files.extend([release_prompt_path, output_path, release_log_path])
            if exit_code != 0:
                raise HarnessError(
                    f"stage-07-release-output: codex exec failed with exit code {exit_code}; "
                    f"see {rel(release_log_path, root)}"
                )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HarnessError("stage-07-release-output: output.md was not produced")
        release_validation = run_release_validators(
            root,
            output_path,
            stage05_per_burden_entries(stage_by_id(stages, "stage-05-mrp-reread-terminal-state")),
        )
        release_field_diagnostics = build_release_field_diagnostics(output_path)
        stage05 = stage_by_id(stages, "stage-05-mrp-reread-terminal-state") or {}
        stage07 = {
            "id": "stage-07-release-output",
            "status": "pass",
            "produces": ["release_output", "release_terminal_states"],
            "requires": ["field_witness_body_refs", "nar_burdens"],
            "release_output": {"path": rel(output_path, root), "sha256": sha256_file(output_path)},
            "release_terminal_states": stage05.get("terminal_states", {}),
            "closure_claim": "complete",
            "output_is_full_governed_answer": True,
            "release_validation": release_validation,
            "release_field_diagnostics": release_field_diagnostics,
            "release_output_mode": release_output_mode,
        }
        if assembly_record is not None:
            stage07["assembly_manifest"] = dict(assembly_record["assembly_manifest"])
            stage07["assembly_hashes"] = dict(assembly_record["hash_record"])
            stage07["target_output_kb"] = int(args.target_output_kb or 0)
        stages.append(stage07)
        if args.stop_after_stage == "stage-07-release-output":
            record["stages"] = stages
            handoff_record = records_dir / "staged-handoff-stage-local-record.json"
            write_json(handoff_record, record)
            validate_replay_record(root, handoff_record)
            hash_path = run_dir / "staged-smoke.hashes.json"
            write_hash_record(
                hash_path,
                root=root,
                case_name=args.case_name,
                mode=mode,
                model=args.model,
                skill_path=files["skill"],
                replay_record=replay_record,
                raw_input_path=raw_input,
                run_dir=run_dir,
                stage_files=stage_files + [handoff_record],
                handoff_record=handoff_record,
                output_path=output_path,
                sidecar_paths=[],
                verdict="STAGED_CURRENT_SKILL_STAGE_LOCAL_PASS: stopped after stage-07-release-output",
            )
            print("staged current-skill stage-local smoke: PASS")
            print(f"run dir: {rel(run_dir, root)}")
            print("stop-after-stage: stage-07-release-output")
            print(f"output: {rel(output_path, root)}")
            print(f"handoff record: {rel(handoff_record, root)}")
            print(f"hashes: {rel(hash_path, root)}")
            return 0

        sidecar_dir = run_dir / "proof-sidecars"
        sidecars = build_sidecars(root=root, raw_input=raw_input, output_path=output_path, out_dir=sidecar_dir, prefix=args.case_name)
        stage08 = {
            "id": "stage-08-verifier-sidecars",
            "status": "pass",
            "produces": ["verifier_sidecars"],
            "requires": ["release_output"],
            "verifier_sidecars": {
                "proof_sidecars": {
                    "claimed": True,
                    "paths": [rel(path_item, root) for path_item in sidecars],
                },
                "b5_4_1": {
                    "claimed": False,
                    "path": rel(sidecars[-1], root),
                    "role": "checker-owned-final-verifier-built-but-not-retained",
                    "non_claims": {"not_fresh_runtime_default_emission": True},
                },
            },
        }
        stages.append(stage08)
        record["stages"] = stages
        handoff_record = records_dir / "staged-handoff-record.json"
        write_json(handoff_record, record)
        validate_replay_record(root, handoff_record)
        hash_path = run_dir / "staged-smoke.hashes.json"
        write_hash_record(
            hash_path,
            root=root,
            case_name=args.case_name,
            mode=mode,
            model=args.model,
            skill_path=files["skill"],
            replay_record=replay_record,
            raw_input_path=raw_input,
            run_dir=run_dir,
            stage_files=stage_files,
            handoff_record=handoff_record,
            output_path=output_path,
            sidecar_paths=sidecars,
            verdict="STAGED_CURRENT_SKILL_ONE_CASE_PROOF_SURFACE_PASS",
        )
        print("staged current-skill smoke: PASS")
        print(f"run dir: {rel(run_dir, root)}")
        print(f"output: {rel(output_path, root)}")
        print(f"handoff record: {rel(handoff_record, root)}")
        print(f"hashes: {rel(hash_path, root)}")
        return 0
    except HarnessError as exc:
        failed_record = dict(record)
        failed_record["stages"] = stages
        failed_record["failure"] = str(exc)
        partial_output_path = run_dir / "output.md"
        if partial_output_path.exists() and partial_output_path.stat().st_size > 0:
            failed_record["stage07_release_field_diagnostics"] = build_release_field_diagnostics(partial_output_path)
        failure_record_path = records_dir / "staged-handoff-failure.json"
        write_json(failure_record_path, failed_record)
        hash_path = run_dir / "staged-smoke.hashes.json"
        write_hash_record(
            hash_path,
            root=root,
            case_name=args.case_name,
            mode="staged-current-skill-smoke",
            model=args.model,
            skill_path=files["skill"],
            replay_record=replay_record,
            raw_input_path=raw_input,
            run_dir=run_dir,
            stage_files=stage_files + [failure_record_path],
            handoff_record=failure_record_path,
            output_path=run_dir / "output.md",
            sidecar_paths=[],
            verdict=f"STAGED_MODEL_HARNESS_NEGATIVE_EVIDENCE: {exc}",
        )
        print("staged current-skill smoke: FAIL")
        print(f"run dir: {rel(run_dir, root)}")
        print(f"failure: {exc}")
        print(f"failure record: {rel(failure_record_path, root)}")
        print(f"hashes: {rel(hash_path, root)}")
        return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--preflight-input-only", action="store_true")
    parser.add_argument("--case-name", default="staged-a9-science-source")
    parser.add_argument("--raw-input", default=None)
    parser.add_argument("--raw-input-path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--replay-record", type=Path, default=DEFAULT_REPLAY_RECORD)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--stop-after-stage", choices=STAGE_ORDER[:7], default=None)
    parser.add_argument("--release-output-mode", choices=sorted(RELEASE_OUTPUT_MODE_ALIASES), default="single-output")
    parser.add_argument("--target-output-kb", type=int, default=0)
    parser.add_argument("--section-expansion-rounds", type=int, default=0)
    parser.add_argument("--transport-retry-rounds", type=int, default=0)
    parser.add_argument("--resume-run-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if Path.cwd().resolve() != root:
        raise HarnessError(
            f"Wrong current directory. Current={Path.cwd().resolve()}; expected root={root}. "
            "Run from the repo root so artifacts cannot bind another workspace."
        )
    if args.section_expansion_rounds < 0:
        raise HarnessError("--section-expansion-rounds must be a non-negative integer")
    if args.transport_retry_rounds < 0:
        raise HarnessError("--transport-retry-rounds must be a non-negative integer")
    if args.self_test:
        return run_self_test(root)
    release_output_mode = normalize_release_output_mode(args.release_output_mode)
    validate_compiled_budget_preflight(
        release_output_mode,
        args.target_output_kb,
        args.section_expansion_rounds,
    )
    if args.preflight_input_only:
        if args.run_dir is None:
            timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
            args.run_dir = root / ".daee" / "staged-current-skill-smokes" / f"{timestamp}-{args.case_name}"
        return preflight_smoke_inputs(args, root)
    if args.resume_run_dir is not None:
        resume_run_dir = resolve_under_root(root, args.resume_run_dir, "Resume run directory")
        if args.run_dir is None:
            args.run_dir = resume_run_dir
        else:
            run_dir = resolve_under_root(root, args.run_dir, "Run directory")
            if run_dir != resume_run_dir:
                raise HarnessError("--resume-run-dir and --run-dir must identify the same directory")
            args.run_dir = run_dir
    if args.run_dir is None:
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        args.run_dir = root / ".daee" / "staged-current-skill-smokes" / f"{timestamp}-{args.case_name}"
    return run_model_smoke(args, root)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        print(f"staged current-skill harness: BLOCKED: {exc}")
        raise SystemExit(2)
