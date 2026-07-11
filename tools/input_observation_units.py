#!/usr/bin/env python3
"""Plan02 input-pressure-v1 observation, candidate, pressure, and burden custody."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any, Iterable

SURFACE_KINDS = {"claim", "question", "contrast", "narrative-context", "conclusion", "instruction", "quote"}
CANDIDATE_STATUSES = {"selected", "held", "underdetermined", "merged", "rejected"}
PRESSURE_STATUSES = {"routed", "merged", "held", "non_load_bearing", "unresolved"}
OBSERVATION_DISPOSITIONS = {"narrative_context", "duplicate", "formatting", "instruction_only", "non_load_bearing"}
OPEN_RELEASE_STATES = {"OPEN", "HOLD", "PARTIAL", "RECURSE"}
B_ID = re.compile(r"^B[1-9][0-9]*$")


def _finding(subcode: str, message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class": "stage02-input-pressure-coverage", "failure_subcode": subcode, "message": message, "markers": list(markers)}


def _slice_sha256(source: str, start: int, end: int) -> str:
    return hashlib.sha256(source[start:end].encode("utf-8")).hexdigest()


def _surface_kind(text: str) -> str:
    stripped = text.strip()
    if stripped.endswith("?"):
        return "question"
    return "claim"


def segment_observation_units(source_text: str) -> list[dict[str, Any]]:
    """Deterministically split nonblank paragraphs and nested quoted spans by codepoint."""
    if not isinstance(source_text, str) or not source_text.strip():
        return []
    units: list[dict[str, Any]] = []
    paragraph_pattern = re.compile(r"\S(?:.*?\S)?(?=(?:\r?\n[ \t]*){2,}|\Z)", re.DOTALL)
    for match in paragraph_pattern.finditer(source_text):
        start, end = match.span()
        unit_id = f"U{len(units) + 1}"
        text = source_text[start:end]
        units.append({"unit_id": unit_id, "source_start": start, "source_end": end, "source_sha256": _slice_sha256(source_text, start, end), "surface_kind": _surface_kind(text), "parent_unit_id": None})
        quote_pattern = re.compile(r'"[^"\r\n]+"|“[^”\r\n]+”')
        for quote in quote_pattern.finditer(text):
            qstart, qend = start + quote.start(), start + quote.end()
            units.append({"unit_id": f"U{len(units) + 1}", "source_start": qstart, "source_end": qend, "source_sha256": _slice_sha256(source_text, qstart, qend), "surface_kind": "quote", "parent_unit_id": unit_id})
    return units


def _validate_string_ids(value: Any, field: str, *, allow_empty: bool = False) -> tuple[list[str] | None, dict[str, Any] | None]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        return None, _finding("collection-shape", f"{field} must be a {'possibly empty ' if allow_empty else 'nonempty '}unique string array", field)
    return value, None


def validate_input_pressure_record(record: Any, *, upstream_source_text: str | None = None) -> list[dict[str, Any]]:
    """Validate the primary Plan02 input-pressure-v1 object without semantic grading."""
    if not isinstance(record, dict):
        return [_finding("record-shape", "record must be an object")]
    if record.get("topology_contract") != "input-pressure-v1":
        return [_finding("contract-version", "topology_contract must be input-pressure-v1")]
    if record.get("offset_unit") != "unicode-codepoint":
        return [_finding("offset-unit", "offset_unit must be unicode-codepoint")]
    source = record.get("source_text")
    if not isinstance(upstream_source_text, str):
        return [_finding("upstream-source-boundary-required", "an independently supplied source text is required", "external", "upstream_source_text")]
    if source != upstream_source_text:
        return [_finding("upstream-source-mismatch", "record source_text differs from the independent source artifact", "external", "source_text")]
    if not isinstance(source, str) or not source.strip():
        return [_finding("empty-input", "release-bearing input must contain a non-whitespace source range", "source_text", "empty")]

    observations = record.get("observation_units")
    if not isinstance(observations, list) or not observations:
        return [_finding("observation-shape", "observation_units must be a nonempty array")]
    observation_ids: set[str] = set()
    ranges: dict[str, tuple[int, int, str | None]] = {}
    for unit in observations:
        if not isinstance(unit, dict):
            return [_finding("observation-shape", "each observation unit must be an object")]
        required = {"unit_id", "source_start", "source_end", "source_sha256", "surface_kind", "parent_unit_id"}
        if not required <= set(unit):
            return [_finding("observation-shape", f"observation unit lacks {sorted(required - set(unit))}")]
        unit_id = unit["unit_id"]
        if not isinstance(unit_id, str) or not unit_id or unit_id in observation_ids:
            return [_finding("observation-id", f"invalid or duplicate observation id {unit_id!r}")]
        observation_ids.add(unit_id)
        start, end, parent = unit["source_start"], unit["source_end"], unit["parent_unit_id"]
        if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or not (0 <= start < end <= len(source)):
            return [_finding("observation-anchor", f"{unit_id} has an empty or out-of-range codepoint anchor", unit_id)]
        if unit["surface_kind"] not in SURFACE_KINDS:
            return [_finding("surface-kind", f"{unit_id} has unsupported surface_kind", unit_id)]
        if unit["source_sha256"] != _slice_sha256(source, start, end):
            return [_finding("observation-hash", f"{unit_id} source_sha256 does not bind its exact UTF-8 slice", unit_id)]
        if parent is not None and (not isinstance(parent, str) or not parent):
            return [_finding("observation-parent", f"{unit_id} parent_unit_id must be null or a nonempty ID", unit_id)]
        ranges[unit_id] = (start, end, parent)
    top_level: list[tuple[int, int, str]] = []
    siblings: dict[str, list[tuple[int, int, str]]] = {}
    for unit_id, (start, end, parent) in ranges.items():
        if parent is None:
            top_level.append((start, end, unit_id))
            continue
        if parent not in ranges:
            return [_finding("observation-parent", f"{unit_id} has dangling parent {parent}", unit_id, parent)]
        pstart, pend, _ = ranges[parent]
        if not (pstart <= start and end <= pend) or (pstart == start and pend == end):
            return [_finding("observation-overlap", f"{unit_id} is not a proper child span of {parent}", unit_id, parent)]
        siblings.setdefault(parent, []).append((start, end, unit_id))
    for spans in [top_level, *siblings.values()]:
        ordered = sorted(spans)
        for left, right in zip(ordered, ordered[1:]):
            if right[0] < left[1]:
                return [_finding("observation-overlap", f"non-parent-child spans {left[2]} and {right[2]} overlap", left[2], right[2])]
    uncovered = [index for index, char in enumerate(source) if not char.isspace() and not any(start <= index < end for start, end, _ in top_level)]
    if uncovered:
        return [_finding("source-range-uncovered", f"non-whitespace codepoint {uncovered[0]} is uncovered", str(uncovered[0]))]

    candidates = record.get("candidate_states")
    if not isinstance(candidates, list) or not candidates:
        return [_finding("candidate-shape", "candidate_states must be a nonempty array")]
    candidate_by_id: dict[str, dict[str, Any]] = {}
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return [_finding("candidate-shape", "candidate state must be an object")]
        required = {"state_id", "observation_unit_ids", "frame", "live_registers", "status", "basis", "merged_into"}
        missing = sorted(required - set(candidate))
        if missing:
            return [_finding("candidate-shape", f"candidate state lacks {missing}", *missing)]
        state_id = candidate["state_id"]
        if not isinstance(state_id, str) or not state_id or state_id in candidate_by_id:
            return [_finding("candidate-id", f"invalid or duplicate state_id {state_id!r}")]
        observation_refs, finding = _validate_string_ids(candidate["observation_unit_ids"], "observation_unit_ids")
        if finding:
            return [finding]
        if not set(observation_refs or []) <= observation_ids:
            return [_finding("candidate-observation-join", f"{state_id} references an unknown observation", state_id)]
        if not isinstance(candidate["live_registers"], list) or not all(isinstance(item, str) and item for item in candidate["live_registers"]) or len(candidate["live_registers"]) != len(set(candidate["live_registers"])):
            return [_finding("candidate-registers", f"{state_id} live_registers must be strings", state_id)]
        if candidate["status"] not in CANDIDATE_STATUSES or not isinstance(candidate["frame"], str) or not candidate["frame"].strip() or not isinstance(candidate["basis"], str) or not candidate["basis"].strip():
            return [_finding("candidate-status", f"{state_id} lacks canonical frame/status/basis", state_id)]
        if candidate["status"] == "merged":
            if not isinstance(candidate["merged_into"], str) or not candidate["merged_into"] or candidate["merged_into"] == state_id:
                return [_finding("candidate-merge-join", f"{state_id} merged state needs a distinct receiver", state_id)]
        elif candidate["merged_into"] is not None:
            return [_finding("candidate-merge-join", f"{state_id} non-merged state cannot name merged_into", state_id)]
        if candidate["status"] == "rejected" and "not selected" in candidate["basis"].lower():
            return [_finding("candidate-circular-basis", f"{state_id} uses circular rejection basis", state_id)]
        candidate_by_id[state_id] = candidate
        if candidate["status"] == "selected":
            selected.append(candidate)
    for state_id, candidate in candidate_by_id.items():
        if candidate["status"] == "merged" and candidate["merged_into"] not in candidate_by_id:
            return [_finding("candidate-merge-join", f"{state_id} receiver {candidate['merged_into']} is absent", state_id, candidate["merged_into"])]
    candidate_partitions = record.get("candidate_state_partitions", [])
    if not isinstance(candidate_partitions, list):
        return [_finding("candidate-merge-join", "candidate_state_partitions must be an array")]
    for state_id, candidate in candidate_by_id.items():
        if candidate["status"] != "merged":
            continue
        proved = any(isinstance(partition, dict) and partition.get("decision") == "merge_equivalent" and state_id in partition.get("merged_state_ids", []) and partition.get("selected_state_id") == candidate["merged_into"] for partition in candidate_partitions)
        if not proved:
            return [_finding("candidate-merge-join", f"{state_id} merged state lacks a proved merge_equivalent decision/receiver", state_id, str(candidate["merged_into"]))]
    selection_status = record.get("selection_status")
    selected_frame = record.get("selected_n_frame")
    if selection_status == "licensed":
        if len(selected) != 1 or selected_frame != selected[0]["frame"]:
            return [_finding("selection-join", "licensed selection requires exactly one matching selected frame")]
    elif selection_status == "not_licensed":
        if selected or selected_frame is not None or not any(item["status"] in {"held", "underdetermined"} for item in candidates):
            return [_finding("selection-not-licensed", "not_licensed requires preserved held/underdetermined candidates and no selection")]
        if record.get("release_state") not in {"OPEN", "PARTIAL"}:
            return [_finding("false-closure", "zero selected candidates require truthful OPEN or PARTIAL", "OPEN", "PARTIAL")]
    else:
        return [_finding("selection-status", "selection_status must be licensed or not_licensed")]

    burden_floor, finding = _validate_string_ids(record.get("burden_floor"), "burden_floor", allow_empty=True)
    if finding:
        return [finding]
    if not all(B_ID.fullmatch(item) for item in burden_floor or []):
        return [_finding("burden-floor-shape", "burden_floor contains an invalid burden ID")]
    origins = record.get("burden_origins")
    if not isinstance(origins, dict) or set(origins) != set(burden_floor or []) or any(value != "B_LA" for value in origins.values()):
        return [_finding("stage02-generated-burden", "every Stage02 burden_floor ID must be frozen as B_LA; B_MRP is Stage05-owned", "B_LA", "B_MRP")]
    decisions = record.get("burden_partition_decisions", [])
    if not isinstance(decisions, list):
        return [_finding("partition-decision-shape", "burden_partition_decisions must be an array")]
    decision_by_id = {item.get("decision_id"): item for item in decisions if isinstance(item, dict) and isinstance(item.get("decision_id"), str)}

    pressures = record.get("input_pressures")
    if not isinstance(pressures, list) or not pressures:
        return [_finding("pressure-shape", "input_pressures must be a nonempty array")]
    pressure_ids: set[str] = set()
    pressure_observations: set[str] = set()
    for pressure in pressures:
        if not isinstance(pressure, dict):
            return [_finding("pressure-shape", "pressure must be an object")]
        required = {"pressure_id", "observation_unit_ids", "candidate_state_ids", "pressure_function", "register_axes", "status", "burden_id", "decision_id", "basis"}
        missing = sorted(required - set(pressure))
        if missing:
            return [_finding("pressure-shape", f"pressure lacks {missing}", *missing)]
        pressure_id = pressure["pressure_id"]
        if not isinstance(pressure_id, str) or not pressure_id or pressure_id in pressure_ids:
            return [_finding("pressure-id", f"invalid or duplicate pressure id {pressure_id!r}")]
        pressure_ids.add(pressure_id)
        observation_refs, finding = _validate_string_ids(pressure["observation_unit_ids"], "observation_unit_ids")
        if finding:
            return [finding]
        candidate_refs, finding = _validate_string_ids(pressure["candidate_state_ids"], "candidate_state_ids")
        if finding:
            return [finding]
        if not set(observation_refs or []) <= observation_ids or not set(candidate_refs or []) <= set(candidate_by_id):
            return [_finding("pressure-source-join", f"{pressure_id} has an unknown observation/candidate reference", pressure_id)]
        if not isinstance(pressure["pressure_function"], str) or not pressure["pressure_function"].strip() or not isinstance(pressure["basis"], str) or not pressure["basis"].strip() or not isinstance(pressure["register_axes"], list) or not all(isinstance(item, str) and item for item in pressure["register_axes"]) or len(pressure["register_axes"]) != len(set(pressure["register_axes"])):
            return [_finding("pressure-shape", f"{pressure_id} lacks function/register/basis", pressure_id)]
        status = pressure["status"]
        if status not in PRESSURE_STATUSES:
            return [_finding("pressure-status", f"{pressure_id} has unsupported status", pressure_id)]
        if status == "routed":
            if pressure["burden_id"] not in set(burden_floor or []):
                return [_finding("routed-burden-join", f"routed pressure {pressure_id} lacks exactly one B_LA burden", pressure_id, str(pressure["burden_id"]))]
        elif status == "merged":
            decision = decision_by_id.get(pressure["decision_id"])
            mappings = decision.get("pressure_to_burden", []) if isinstance(decision, dict) else []
            if pressure["burden_id"] not in set(burden_floor or []) or not decision or not any(isinstance(item, dict) and item.get("pressure_id") == pressure_id and item.get("burden_id") == pressure["burden_id"] for item in mappings):
                return [_finding("merged-pressure-join", f"merged pressure {pressure_id} lacks a proved decision/receiver", pressure_id, str(pressure["decision_id"]))]
        elif status == "held":
            if not str(pressure.get("gate", "")).strip() or not str(pressure.get("next_action", "")).strip():
                return [_finding("held-pressure-custody", f"held pressure {pressure_id} needs gate and next_action", pressure_id, "gate", "next_action")]
        elif status == "unresolved" and record.get("release_state") not in {"PARTIAL", "RECURSE"}:
            return [_finding("unresolved-pressure-closure", f"unresolved pressure {pressure_id} forces PARTIAL or RECURSE", pressure_id, "PARTIAL", "RECURSE")]
        if status in {"held", "non_load_bearing", "unresolved"} and pressure["burden_id"] is not None:
            return [_finding("pressure-burden-join", f"{status} pressure {pressure_id} cannot claim a routed burden", pressure_id)]
        pressure_observations.update(observation_refs or [])

    dispositions = record.get("observation_dispositions", [])
    if not isinstance(dispositions, list):
        return [_finding("observation-disposition-shape", "observation_dispositions must be an array")]
    disposed: set[str] = set()
    for disposition in dispositions:
        if not isinstance(disposition, dict) or disposition.get("disposition") not in OBSERVATION_DISPOSITIONS or disposition.get("unit_id") not in observation_ids or not str(disposition.get("basis", "")).strip():
            return [_finding("observation-disposition", "invalid explicit observation disposition")]
        if disposition["unit_id"] in disposed:
            return [_finding("observation-disposition", f"observation {disposition['unit_id']} has duplicate explicit dispositions", disposition["unit_id"])]
        disposed.add(disposition["unit_id"])
    unaccounted = observation_ids - pressure_observations - disposed
    if unaccounted:
        missing = sorted(unaccounted)[0]
        return [_finding("observation-unaccounted", f"observation {missing} disappears before pressure accounting", missing, "observation-unaccounted")]
    coverage = record.get("input_coverage")
    expected = {"all_observation_unit_ids": sorted(observation_ids), "pressure_bearing_unit_ids": sorted(pressure_observations), "explicitly_disposed_unit_ids": sorted(disposed), "unaccounted_unit_ids": []}
    if not isinstance(coverage, dict) or any(not isinstance(coverage.get(key), list) or not all(isinstance(item, str) for item in coverage[key]) for key in expected) or {key: sorted(coverage[key]) for key in expected} != expected:
        return [_finding("coverage-mismatch", "declared input_coverage does not equal derived set accounting")]
    if any(item["status"] in {"held", "unresolved"} for item in pressures) and record.get("release_state") == "COMPLETE":
        return [_finding("false-closure", "held or unresolved pressure cannot coexist with COMPLETE")]
    return []


def _self_test() -> int:
    source = 'alpha\r\n\r\n"beta"'
    units = segment_observation_units(source)
    parent_ids = [item["unit_id"] for item in units if item["parent_unit_id"] is None]
    quote = next(item for item in units if item["surface_kind"] == "quote")
    ok = len(parent_ids) == 2 and quote["parent_unit_id"] == parent_ids[1] and source[quote["source_start"]:quote["source_end"]] == '"beta"' and segment_observation_units("") == []
    print(json.dumps({"checker_id": "input-observation-units", "status": "PASS" if ok else "FAIL", "offset_unit": "unicode-codepoint"}, sort_keys=True))
    return 0 if ok else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.error("input_observation_units is a pure library; use --self-test or import it")


if __name__ == "__main__":
    raise SystemExit(main())
