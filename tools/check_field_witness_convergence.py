#!/usr/bin/env python3
"""Validate field_witness graph/register convergence.

This checker is deliberately narrower than the runtime. It does not infer
whether the answer is theologically adequate. It checks whether the final
field_witness can serve as a convergence certificate for the burdens already
named by Layer A/register state and by generated MRP provenance.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    BURDEN_ID_RE,
    burden_ids,
    closure_witness_errors,
    compare_visible_to_field_witness,
    extract_embedded_field_witness,
    extract_closure_witness_block,
    extract_field_witness,
    field_witness_graph_errors,
    field_witness_ledger,
    field_witness_mrp_resultants,
    normalize_burden_id,
    parse_closure_witness,
    public_graph_integrity_diagnostics,
    status_head,
    terminal_public_order_diagnostics,
    unique,
)
from witness_artifact_roles import validate_role


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "field-witness-convergence"
FORMALISM_NEUTRAL_INVALID_DIR = ROOT / "tests" / "formalism-path-neutral" / "invalid"

CLOSED_TERMINAL_STATES = {
    "landed",
    "cleared",
    "discharged-as-derivative",
    "held-with-reason",
}
LIVE_TERMINAL_STATES = {"carried-PARTIAL", "carried-RECURSE"}
EDGE_REQUIRING_RESULTANT_TYPES = {"held_burden_activation", "generated_burden_instantiation"}
B_TOTAL_LEDGER_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:𝔅_total\s*\(\s*)?B_total\s*\)?\s*(?:=|:)\s*\S"
)
B_LA_LEDGER_RE = re.compile(
    r"(?i)^\s*(?:[-*]\s*)?(?:𝔅_LA\s*\(\s*)?B_LA\s*\)?\s*(?:=|:)\s*\S"
)

REGISTER_ALIASES = {
    "omega": "Omega",
    "Ω": "Omega",
    "ontological": "Omega",
    "ontology": "Omega",
    "predication": "Omega",
    "xi": "xi",
    "ξ": "xi",
    "warrant": "xi",
    "authority": "xi",
    "source-order": "xi",
    "source order": "xi",
    "mu": "mu",
    "μ": "mu",
    "memetic": "mu",
    "carrier": "mu",
    "default-carrier": "mu",
    "kappa": "kappa",
    "κ": "kappa",
    "dependency": "kappa",
    "collapse": "kappa",
    "implication-chain": "kappa",
    "implication chain": "kappa",
    "heart": "heart",
    "♥": "heart",
    "affective": "heart",
    "posture": "heart",
}

REGISTER_BURDEN_KEYWORDS = {
    "Omega": (
        "omega",
        "ontolog",
        "predication",
        "worldview",
        "source-worldview",
        "metaphysic",
        "predicate",
        "parsimony",
        "simplicity",
        "person-nature",
        "nature",
    ),
    "xi": (
        "xi",
        "warrant",
        "authority",
        "source-order",
        "source order",
        "source-status",
        "tribunal",
        "testimony",
    ),
    "mu": (
        "mu",
        "memetic",
        "carrier",
        "compression",
        "stabilizer",
        "decompose",
        "decomposition",
        "default-carrier",
    ),
    "kappa": (
        "kappa",
        "dependency",
        "collapse",
        "implication-chain",
        "implication chain",
        "entailment",
        "downstream",
        "chain",
        "curl",
        "loop",
        "circular",
        "doubt-churn",
        "proof-carousel",
        "deception-loop",
    ),
    "heart": (
        "heart",
        "affective",
        "posture",
        "security",
        "confidence",
        "grief",
        "recoil",
    ),
}

REGISTER_LABELS = {
    "Omega": "ontological/predication",
    "xi": "warrant/authority/source-order",
    "mu": "memetic-carrier",
    "kappa": "dependency/collapse",
    "heart": "affective/posture",
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def extract_layer_a(text: str) -> str:
    match = re.search(r"(?im)^\s*#{0,6}\s*Layer A\b.*$", text)
    if not match:
        return ""
    end_match = re.search(r"(?im)^\s*#{0,6}\s*Layer B\b.*$", text[match.end() :])
    end = match.end() + end_match.start() if end_match else len(text)
    return text[match.end() : end]


def line_body(line: str) -> str:
    if ":" in line:
        return line.split(":", 1)[1]
    if "=" in line:
        return line.split("=", 1)[1]
    return line


def layer_a_obligations(text: str) -> dict[str, list[str]]:
    layer = extract_layer_a(text)
    obligations = {
        "initial": [],
        "B_LA": [],
        "live": [],
        "held": [],
        "mentioned": [],
    }
    if not layer:
        return obligations

    initial_match = re.search(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]", layer)
    if initial_match:
        obligations["initial"] = unique(burden_ids(initial_match.group("body")))

    for line in layer.splitlines():
        if B_LA_LEDGER_RE.search(line):
            obligations["B_LA"] = unique(burden_ids(line_body(line)))
        if re.search(r"(?i)\blive noetic burden\b", line):
            obligations["live"].extend(burden_ids(line_body(line)))
        if re.search(r"(?i)^\s*(?:[-*]\s*)?held\s*:", line):
            obligations["held"].extend(burden_ids(line_body(line)))

    obligations["live"] = unique(obligations["live"])
    obligations["held"] = unique(obligations["held"])
    obligations["mentioned"] = unique(obligations["initial"] + obligations["B_LA"] + obligations["live"] + obligations["held"])
    return obligations


def canonical_register(raw: str) -> str:
    key = str(raw or "").strip()
    if not key:
        return ""
    return REGISTER_ALIASES.get(key, REGISTER_ALIASES.get(key.lower(), key))


def registers_in_text(text: str) -> list[str]:
    found: list[str] = []
    source = str(text or "")
    lowered = source.lower()
    for alias, register in REGISTER_ALIASES.items():
        if len(alias) == 1 and alias not in source:
            continue
        if len(alias) > 1 and not re.search(rf"(?i)(?<![A-Za-z0-9_-]){re.escape(alias)}(?![A-Za-z0-9_-])", source):
            continue
        if register not in found:
            found.append(register)
    for register, keywords in REGISTER_BURDEN_KEYWORDS.items():
        if any(register_keyword_in_text(keyword, lowered) for keyword in keywords) and register not in found:
            found.append(register)
    return found


def register_keyword_in_text(keyword: str, lowered_text: str) -> bool:
    lowered_keyword = keyword.lower()
    if re.fullmatch(r"[a-z]{1,3}", lowered_keyword):
        return bool(
            re.search(
                rf"(?<![a-z0-9_-]){re.escape(lowered_keyword)}(?![a-z0-9_-])",
                lowered_text,
            )
        )
    return lowered_keyword in lowered_text


def live_register_obligations(text: str) -> list[str]:
    layer = extract_layer_a(text)
    found: list[str] = []
    for line in layer.splitlines():
        label = re.sub(r"^\s*(?:[-*]\s*)?", "", line).strip()
        if not (
            re.search(r"(?i)^live\s+noetic\s+burden\s*[:=]", label)
            or re.search(r"(?i)^live\s+registers?\s*[:=]", label)
            or re.search(r"(?i)^live_registers\s*[:=]", label)
            or (re.search(r"(?i)^IR\(N", label) and re.search(r"(?i)\blive\b", label))
        ):
            continue
        if not re.search(r"(?i)\blive\b|IR\(N", line):
            continue
        candidate = line_body(line)
        candidate = re.sub(r"(?i)\bIR\(N[^)]*\)", "", candidate)
        candidate = re.split(r"(?i)\bare\s+live\b", candidate, maxsplit=1)[0]
        if "live_registers" in line and "=" in candidate:
            candidate = candidate.split("=", 1)[1]
        for register in registers_in_text(candidate):
            if register not in found:
                found.append(register)
    return found


def list_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;/|]+", value) if part.strip()]
    return []


def node_payloads(field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    raw_nodes = field_witness.get("nodes")
    if not isinstance(raw_nodes, list):
        return payloads
    for item in raw_nodes:
        if isinstance(item, dict):
            burden = normalize_burden_id(str(item.get("id") or ""))
            if BURDEN_ID_RE.fullmatch(burden):
                payloads[burden] = item
    return payloads


def explicit_node_registers(node: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for key in ("register_types", "registers", "burden_types", "types"):
        for value in list_values(node.get(key)):
            register = canonical_register(value)
            if register in REGISTER_BURDEN_KEYWORDS and register not in found:
                found.append(register)
    return found


def inferred_node_registers(node: dict[str, Any], terminal: dict[str, str] | None = None) -> list[str]:
    del terminal
    explicit = explicit_node_registers(node)
    return explicit


def non_load_bearing_register_proof(text: str, register: str) -> bool:
    label_terms = [register] + [
        alias for alias, mapped in REGISTER_ALIASES.items() if mapped == register and len(alias) > 1
    ]
    pattern = "|".join(re.escape(term) for term in label_terms)
    return bool(
        pattern
        and re.search(
            rf"(?is)(?:{pattern}).{{0,160}}\b(?:non[- ]load[- ]bearing|not load[- ]bearing|outside scope|held-with-reason|carried-PARTIAL)\b|"
            rf"\b(?:non[- ]load[- ]bearing|not load[- ]bearing|outside scope|held-with-reason|carried-PARTIAL)\b.{{0,160}}(?:{pattern})",
            text,
        )
    )


def register_floor_coverage(field_witness: dict[str, Any], terminals: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    ledgers = field_witness_ledger(field_witness)
    floor = ledgers["B_LA"] or ledgers["B_total"]
    nodes = node_payloads(field_witness)
    coverage_by_register: dict[str, list[str]] = {register: [] for register in REGISTER_BURDEN_KEYWORDS}
    for burden in floor:
        node = nodes.get(burden, {"id": burden})
        registers = inferred_node_registers(node, terminals.get(burden))
        for register in registers:
            if register in coverage_by_register and burden not in coverage_by_register[register]:
                coverage_by_register[register].append(burden)
    return coverage_by_register


def diagnostic_completeness_errors(
    path: Path,
    field_witness: dict[str, Any],
    live_registers: list[str],
    register_coverage: dict[str, list[str]],
    strict: bool,
) -> list[str]:
    if not live_registers:
        return []
    prefix = f"{rel(path)}: "
    cov = coverage(field_witness)
    raw = cov.get("diagnostic_completeness")
    if raw is None:
        if strict:
            return [prefix + "coverage_proof.diagnostic_completeness missing for live register proof"]
        return []
    if not isinstance(raw, dict):
        return [prefix + "coverage_proof.diagnostic_completeness must be an object"]

    claimed_live = []
    for value in list_values(raw.get("live_registers")):
        register = canonical_register(value)
        if register in REGISTER_BURDEN_KEYWORDS and register not in claimed_live:
            claimed_live.append(register)
    if set(claimed_live) != set(live_registers):
        return [
            prefix
            + f"coverage_proof.diagnostic_completeness.live_registers {claimed_live} must cover exactly Layer A live registers {live_registers}"
        ]

    raw_coverage = raw.get("coverage") or raw.get("coverage_mapping") or raw.get("register_coverage")
    if not isinstance(raw_coverage, dict):
        return [prefix + "coverage_proof.diagnostic_completeness.coverage mapping missing"]

    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    floor = set(ledgers["B_LA"] or ledgers["B_total"])
    for register in live_registers:
        key_candidates = [register] + [
            alias for alias, mapped in REGISTER_ALIASES.items() if mapped == register
        ]
        raw_burdens: Any = None
        for key in key_candidates:
            if key in raw_coverage:
                raw_burdens = raw_coverage[key]
                break
        claimed_burdens = unique(
            normalize_burden_id(str(item))
            for item in list_values(raw_burdens)
            if BURDEN_ID_RE.fullmatch(normalize_burden_id(str(item)))
        )
        if not claimed_burdens:
            errors.append(prefix + f"diagnostic_completeness omits live register {register} coverage")
            continue
        for burden in claimed_burdens:
            if burden not in floor:
                errors.append(prefix + f"diagnostic_completeness maps live register {register} to non-floor burden {burden}")
            if burden not in register_coverage.get(register, []):
                errors.append(prefix + f"diagnostic_completeness maps live register {register} to burden {burden} without matching burden type")
    if raw.get("complete") is False:
        errors.append(prefix + "diagnostic_completeness.complete=false cannot support complete register floor")
    return errors


def coverage(field_witness: dict[str, Any]) -> dict[str, Any]:
    value = field_witness.get("coverage_proof")
    return value if isinstance(value, dict) else {}


def int_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def normalize_edges(raw_edges: Any) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    if not isinstance(raw_edges, list):
        return edges
    for edge in raw_edges:
        source: Any
        target: Any
        if isinstance(edge, dict):
            source = edge.get("from")
            target = edge.get("to")
        elif isinstance(edge, list) and len(edge) == 2:
            source, target = edge
        else:
            continue
        if isinstance(source, str) and isinstance(target, str):
            source_id = normalize_burden_id(source.strip())
            target_id = normalize_burden_id(target.strip())
            if BURDEN_ID_RE.fullmatch(source_id) and BURDEN_ID_RE.fullmatch(target_id):
                edges.append((source_id, target_id))
    return unique_edges(edges)


def unique_edges(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for edge in edges:
        if edge not in seen:
            seen.add(edge)
            result.append(edge)
    return result


def graph_nodes(field_witness: dict[str, Any]) -> list[str]:
    graph = coverage(field_witness).get("dependency_graph")
    if not isinstance(graph, dict):
        return []
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, list):
        return []
    return unique(
        normalize_burden_id(str(node))
        for node in raw_nodes
        if isinstance(node, str) and BURDEN_ID_RE.fullmatch(normalize_burden_id(node))
    )


def terminal_payloads(field_witness: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw = coverage(field_witness).get("terminal_states")
    if not isinstance(raw, dict):
        raw = field_witness.get("terminal_states")
    if not isinstance(raw, dict):
        return {}

    terminals: dict[str, dict[str, str]] = {}
    for raw_burden, raw_payload in raw.items():
        burden = normalize_burden_id(str(raw_burden))
        if not BURDEN_ID_RE.fullmatch(burden):
            continue
        if isinstance(raw_payload, dict):
            state = str(raw_payload.get("state") or raw_payload.get("status") or "").strip()
            detail_parts = [
                str(value).strip()
                for key, value in raw_payload.items()
                if key not in {"state", "status"} and value is not None and str(value).strip()
            ]
            terminals[burden] = {"state": state, "detail": " / ".join(detail_parts)}
        else:
            text = str(raw_payload).strip()
            state, _, detail = text.partition("/")
            terminals[burden] = {"state": state.strip(), "detail": detail.strip()}
    return terminals


def closure_text(field_witness: dict[str, Any]) -> str:
    raw = field_witness.get("closure")
    if isinstance(raw, dict):
        return " ".join(str(value) for value in raw.values())
    return str(raw or "")


def complete_claimed(field_witness: dict[str, Any]) -> bool:
    cov = coverage(field_witness)
    if cov.get("coverage_complete") is True:
        return True
    if field_witness.get("collapse_complete") is True:
        return True
    text = closure_text(field_witness)
    return bool(re.search(r"(?i)\bcoverage_complete\s*=\s*true\b|\bclosure\.status\s*=\s*COMPLETE\b|\bstatus\s*=\s*COMPLETE\b", text))


def diagnostic_status(field_witness: dict[str, Any], *keys: str) -> str:
    cov = coverage(field_witness)
    for key in keys:
        value = cov.get(key)
        if isinstance(value, str) and value.strip():
            return value
    diagnostics = field_witness.get("field_diagnostics")
    if isinstance(diagnostics, dict):
        for key in keys:
            value = diagnostics.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in diagnostics.values():
            if not isinstance(value, dict):
                continue
            for key in keys:
                nested = value.get(key)
                if isinstance(nested, str) and nested.strip():
                    return nested
    return ""


def generated_source(value: Any) -> str:
    match = re.search(r"(?i)\bMRP\((?P<source>[^)]+)\)", str(value or ""))
    if not match:
        return ""
    return normalize_burden_id(match.group("source").strip())


def generated_burden_sources(field_witness: dict[str, Any]) -> dict[str, str]:
    sources: dict[str, str] = {}
    raw = field_witness.get("generated_burdens")
    if isinstance(raw, dict):
        for raw_burden, raw_payload in raw.items():
            burden = normalize_burden_id(str(raw_burden))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            generated_by = raw_payload.get("generated_by") if isinstance(raw_payload, dict) else raw_payload
            source = generated_source(generated_by)
            if source:
                sources[burden] = source
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            raw_burden = item.get("id") or item.get("burden") or item.get("target")
            burden = normalize_burden_id(str(raw_burden or ""))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            source = generated_source(item.get("generated_by"))
            if source:
                sources[burden] = source

    raw_nodes = field_witness.get("nodes")
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(str(item.get("id") or ""))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            if str(item.get("type") or "").strip() != "generated_burden" and "generated_by" not in item:
                continue
            source = generated_source(item.get("generated_by"))
            if source and burden not in sources:
                sources[burden] = source
    return sources


def generated_burden_records(field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    raw = field_witness.get("generated_burdens")
    if isinstance(raw, dict):
        for raw_burden, raw_payload in raw.items():
            burden = normalize_burden_id(str(raw_burden))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            payload = raw_payload if isinstance(raw_payload, dict) else {"generated_by": raw_payload}
            records[burden] = {
                "source": generated_source(payload.get("generated_by")),
                "depth": int_value(payload.get("generation_depth")),
                "has_depth": "generation_depth" in payload,
            }
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            raw_burden = item.get("id") or item.get("burden") or item.get("target")
            burden = normalize_burden_id(str(raw_burden or ""))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            records[burden] = {
                "source": generated_source(item.get("generated_by")),
                "depth": int_value(item.get("generation_depth")),
                "has_depth": "generation_depth" in item,
            }

    raw_nodes = field_witness.get("nodes")
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(str(item.get("id") or ""))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            if str(item.get("type") or "").strip() != "generated_burden" and "generated_by" not in item:
                continue
            record = records.setdefault(burden, {"source": "", "depth": None, "has_depth": False})
            source = generated_source(item.get("generated_by"))
            if source and not record.get("source"):
                record["source"] = source
            if "generation_depth" in item:
                node_depth = int_value(item.get("generation_depth"))
                if record.get("depth") is None:
                    record["depth"] = node_depth
                record["has_depth"] = True
    return records


def depth_contract_required(path: Path, field_witness: dict[str, Any]) -> bool:
    ledgers = field_witness_ledger(field_witness)
    records = generated_burden_records(field_witness)
    if ledgers["B_MRP"] or records:
        return True
    cov = coverage(field_witness)
    if "max_generation_depth" in cov:
        return True
    return any(record.get("has_depth") for record in records.values())


def generation_depth_errors(path: Path, field_witness: dict[str, Any], strict: bool) -> list[str]:
    errors: list[str] = []
    prefix = f"{rel(path)}: "
    ledgers = field_witness_ledger(field_witness)
    records = generated_burden_records(field_witness)
    cov = coverage(field_witness)
    depth_by_burden: dict[str, int] = {burden: 0 for burden in ledgers["B_LA"]}
    concrete_depths: list[int] = [0]

    for burden in ledgers["B_MRP"]:
        record = records.get(burden)
        if record is None:
            if strict:
                errors.append(prefix + f"B_MRP burden {burden} lacks generated_burdens generation_depth record")
            continue
        if not record.get("has_depth"):
            if strict:
                errors.append(prefix + f"B_MRP burden {burden} lacks generation_depth")
            continue
        depth = record.get("depth")
        if depth is None:
            errors.append(prefix + f"B_MRP burden {burden} generation_depth must be a non-negative integer")
            continue
        depth_by_burden[burden] = depth
        concrete_depths.append(depth)

    for burden in ledgers["B_MRP"]:
        record = records.get(burden)
        if not record or record.get("depth") is None:
            continue
        source = str(record.get("source") or "")
        if not source:
            continue
        parent_depth = depth_by_burden.get(source)
        if parent_depth is None:
            parent_depth = 0 if source in ledgers["B_LA"] else None
        if parent_depth is None:
            continue
        child_depth = int(record["depth"])
        if child_depth <= parent_depth:
            errors.append(
                prefix + f"B_MRP burden {burden} generation_depth {child_depth} must be greater than parent {source} depth {parent_depth}"
            )

    max_depth_value = cov.get("max_generation_depth")
    if strict and "max_generation_depth" not in cov:
        errors.append(prefix + "coverage_proof.max_generation_depth missing")
        return errors
    if "max_generation_depth" in cov:
        max_depth = int_value(max_depth_value)
        if max_depth is None:
            errors.append(prefix + "coverage_proof.max_generation_depth must be a non-negative integer")
        else:
            expected = max(concrete_depths)
            if max_depth != expected:
                errors.append(
                    prefix + f"coverage_proof.max_generation_depth {max_depth} does not match generated burden max depth {expected}"
                )
    return errors


def resultant_has_edge(resultant: dict[str, str], source: str, target: str) -> bool:
    graph = str(resultant.get("graph") or "")
    normalized = graph.replace("→", "->").replace(" ", "")
    return f"{source}->{target}" in normalized


def resultant_edges(resultant: dict[str, str]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    graph = str(resultant.get("graph") or "")
    if not graph or graph.lower().strip() == "none":
        return edges
    for match in re.finditer(r"\b(B\d+)\b\s*(?:->|→)\s*\b(B\d+)\b", graph):
        source = normalize_burden_id(match.group(1))
        target = normalize_burden_id(match.group(2))
        if BURDEN_ID_RE.fullmatch(source) and BURDEN_ID_RE.fullmatch(target):
            edges.append((source, target))
    return unique_edges(edges)


def resultant_graph_edges(resultants: list[dict[str, str]]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for resultant in resultants:
        edges.extend(resultant_edges(resultant))
    return unique_edges(edges)


def owner_activation_targets(field_witness: dict[str, Any]) -> set[str]:
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return set()
    targets: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        target = normalize_burden_id(str(item.get("target") or ""))
        if BURDEN_ID_RE.fullmatch(target):
            targets.add(target)
    return targets


def normalized_record_required(path: Path, field_witness: dict[str, Any]) -> bool:
    if "normalized_activation_record" in field_witness:
        return True
    cov = coverage(field_witness)
    if cov.get("normalized_activation_record_required") is True:
        return True
    proof_mode = field_witness.get("canonical_ir_projection")
    if isinstance(proof_mode, dict) and proof_mode.get("normalized_activation_record_required") is True:
        return True
    return False


def diagnostic_completeness_required(
    field_witness: dict[str, Any],
    live_registers: list[str],
    register_coverage: dict[str, list[str]],
) -> bool:
    cov = coverage(field_witness)
    if cov.get("diagnostic_completeness") is not None:
        return True
    if live_registers:
        return True
    return any(register_coverage.values())


def normalized_free_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def delta_result_text(value: Any) -> str:
    text = str(value or "").strip()
    if ":" in text:
        return normalized_free_text(text.split(":", 1)[1])
    text = text.replace("¹", "1").replace("²", "2").replace("³", "3")
    patterns = [
        r"(?i)^\s*(?:delta|δ|Δ)\s*\(\s*B\s*\d+\s*\)\s*:?\s*",
        r"(?i)^\s*(?:delta|δ|Δ)\s+B\s*\d+\s*:?\s*",
        r"(?i)^\s*(?:delta|δ|Δ)\s*B?\s*\d+\s*:?\s*",
        r"(?i)^\s*(?:delta|δ|Δ)\s*(?:κ|kappa)\s*:?\s*",
    ]
    for pattern in patterns:
        stripped = re.sub(pattern, "", text, count=1)
        if stripped != text:
            return normalized_free_text(stripped)
    return normalized_free_text(text)


def owner_activation_records_by_target(field_witness: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    records: dict[str, list[dict[str, str]]] = {}
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return records
    for item in raw:
        if not isinstance(item, dict):
            continue
        target = normalize_burden_id(str(item.get("target") or ""))
        if not BURDEN_ID_RE.fullmatch(target):
            continue
        records.setdefault(target, []).append(
            {
                "owner": normalized_free_text(item.get("owner")),
                "operation": normalized_free_text(item.get("operation")),
                "delta_result": delta_result_text(item.get("delta")),
            }
        )
    return records


def mrp_route_types_by_burden(resultants: list[dict[str, str]]) -> dict[str, set[str]]:
    route_types: dict[str, set[str]] = {}
    for resultant in resultants:
        route_type = str(resultant.get("type") or "").strip()
        if not route_type:
            continue
        source = normalize_burden_id(str(resultant.get("source") or ""))
        if BURDEN_ID_RE.fullmatch(source):
            route_types.setdefault(source, set()).add(route_type)
        for _edge_source, target in resultant_edges(resultant):
            route_types.setdefault(target, set()).add(route_type)
    return route_types


def normalized_activation_record_errors(
    path: Path,
    field_witness: dict[str, Any],
    live_registers: list[str],
    strict: bool,
) -> list[str]:
    prefix = f"{rel(path)}: "
    raw = field_witness.get("normalized_activation_record")
    if raw is None:
        if strict:
            return [prefix + "field_witness.normalized_activation_record missing"]
        return []
    if not isinstance(raw, dict):
        return [prefix + "field_witness.normalized_activation_record must be an object"]

    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    terminals = terminal_payloads(field_witness)
    activations_by_target = owner_activation_records_by_target(field_witness)
    resultants = field_witness_mrp_resultants(field_witness)
    route_types_by_burden = mrp_route_types_by_burden(resultants)
    generated_records = generated_burden_records(field_witness)
    expected_depths: dict[str, int] = {burden: 0 for burden in ledgers["B_LA"]}
    for burden, record in generated_records.items():
        depth = record.get("depth")
        if isinstance(depth, int):
            expected_depths[burden] = depth

    if not str(raw.get("n_frame") or "").strip():
        errors.append(prefix + "normalized_activation_record.n_frame missing")

    if live_registers:
        claimed_live = []
        for value in list_values(raw.get("live_registers")):
            register = canonical_register(value)
            if register in REGISTER_BURDEN_KEYWORDS and register not in claimed_live:
                claimed_live.append(register)
        if set(claimed_live) != set(live_registers):
            errors.append(
                prefix
                + f"normalized_activation_record.live_registers {claimed_live} must match Layer A live registers {live_registers}"
            )

    claimed_floor = [
        normalize_burden_id(str(item))
        for item in list_values(raw.get("burden_floor"))
        if BURDEN_ID_RE.fullmatch(normalize_burden_id(str(item)))
    ]
    if claimed_floor != ledgers["B_LA"]:
        errors.append(
            prefix + f"normalized_activation_record.burden_floor {claimed_floor} must equal field_witness B_LA {ledgers['B_LA']}"
        )

    per_burden = raw.get("per_burden")
    if not isinstance(per_burden, list):
        errors.append(prefix + "normalized_activation_record.per_burden must be a list")
        return errors

    seen_burdens: set[str] = set()
    seen_signatures: set[tuple[str, str, str, str]] = set()
    expected_signatures = {
        (burden, activation["owner"], activation["operation"], activation["delta_result"])
        for burden, activations in activations_by_target.items()
        for activation in activations
        if burden in ledgers["B_total"]
    }
    for index, item in enumerate(per_burden):
        if not isinstance(item, dict):
            errors.append(prefix + f"normalized_activation_record.per_burden[{index}] must be an object")
            continue
        burden = normalize_burden_id(str(item.get("burden_id") or item.get("id") or item.get("burden") or ""))
        if not BURDEN_ID_RE.fullmatch(burden):
            errors.append(prefix + f"normalized_activation_record.per_burden[{index}] burden_id invalid")
            continue
        seen_burdens.add(burden)
        if burden not in ledgers["B_total"]:
            errors.append(prefix + f"normalized_activation_record.per_burden names {burden} outside B_total")

        matching_activations = activations_by_target.get(burden, [])
        owner = normalized_free_text(item.get("owner_id") or item.get("owner"))
        if not owner:
            errors.append(prefix + f"normalized_activation_record[{burden}].owner_id missing")
        elif matching_activations and owner not in {activation["owner"] for activation in matching_activations}:
            errors.append(prefix + f"normalized_activation_record[{burden}].owner_id does not match owner_activations")

        operation = normalized_free_text(item.get("operation") or item.get("operation_family"))
        if not operation:
            errors.append(prefix + f"normalized_activation_record[{burden}].operation missing")
        elif matching_activations and operation not in {activation["operation"] for activation in matching_activations}:
            errors.append(prefix + f"normalized_activation_record[{burden}].operation does not match owner_activations")

        delta_result = normalized_free_text(item.get("delta_result"))
        if not delta_result:
            errors.append(prefix + f"normalized_activation_record[{burden}].delta_result missing")
        elif matching_activations and delta_result not in {activation["delta_result"] for activation in matching_activations}:
            errors.append(prefix + f"normalized_activation_record[{burden}].delta_result does not match owner_activations")

        signature = (burden, owner, operation, delta_result)
        if all(signature):
            if signature in seen_signatures:
                errors.append(prefix + f"normalized_activation_record.per_burden duplicates activation {burden}/{owner}/{operation}/{delta_result}")
            seen_signatures.add(signature)
            if matching_activations and signature not in expected_signatures:
                errors.append(prefix + f"normalized_activation_record[{burden}] row does not match any owner_activations row")

        route_type = str(item.get("mrp_route_result_type") or item.get("route_result_type") or "").strip()
        if not route_type:
            errors.append(prefix + f"normalized_activation_record[{burden}].mrp_route_result_type missing")
        elif route_types_by_burden.get(burden) and route_type not in route_types_by_burden[burden]:
            errors.append(prefix + f"normalized_activation_record[{burden}].mrp_route_result_type does not match MRP resultants")

        terminal_state = str(item.get("terminal_state") or "").strip()
        expected_terminal = terminals.get(burden, {}).get("state", "")
        if not terminal_state:
            errors.append(prefix + f"normalized_activation_record[{burden}].terminal_state missing")
        elif expected_terminal and terminal_state != expected_terminal:
            errors.append(prefix + f"normalized_activation_record[{burden}].terminal_state does not match terminal_states")

        depth = int_value(item.get("generation_depth"))
        if depth is None:
            errors.append(prefix + f"normalized_activation_record[{burden}].generation_depth must be a non-negative integer")
        elif burden in expected_depths and depth != expected_depths[burden]:
            errors.append(prefix + f"normalized_activation_record[{burden}].generation_depth does not match generated_burdens/B_LA depth")

    missing = [burden for burden in ledgers["B_total"] if burden not in seen_burdens]
    extra = [burden for burden in seen_burdens if burden not in ledgers["B_total"]]
    if missing:
        errors.append(prefix + f"normalized_activation_record.per_burden missing B_total burdens {missing}")
    if extra:
        errors.append(prefix + f"normalized_activation_record.per_burden has burdens outside B_total {extra}")
    missing_activations = sorted(expected_signatures - seen_signatures)
    if missing_activations:
        formatted = ["/".join(signature) for signature in missing_activations]
        errors.append(prefix + f"normalized_activation_record.per_burden missing owner_activations rows {formatted}")
    return errors


def root_burden_node_ids(field_witness: dict[str, Any]) -> list[str]:
    raw = field_witness.get("nodes")
    if not isinstance(raw, list):
        return []
    ids: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        node_id = normalize_burden_id(str(item.get("id") or ""))
        if not BURDEN_ID_RE.fullmatch(node_id):
            continue
        node_type = str(item.get("type") or "").strip()
        if node_type in {"", "burden", "generated_burden"}:
            ids.append(node_id)
    return unique(ids)


def public_graph_contract_diagnostics(field_witness: Any, *, compatibility: str) -> list[dict[str, Any]]:
    """Dispatch current graphs to the public schema and legacy graphs to a labeled adapter."""
    role_diagnostics = [item.to_dict() for item in validate_role(field_witness, "public_graph", compatibility)]
    blocking = [item for item in role_diagnostics if not item.get("failure_subcode", "").startswith("witness-role-historical-")]
    if blocking:
        return blocking
    return public_graph_integrity_diagnostics(field_witness, compatibility=compatibility)


def current_public_convergence_errors(
    path: Path,
    text: str,
    field_witness: dict[str, Any],
) -> list[str]:
    """Check current public-graph convergence without applying historical shape rules."""

    prefix = f"{rel(path)}: "
    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    b_total = ledgers["B_total"]
    b_total_set = set(b_total)
    coverage_payload = coverage(field_witness)
    dependency_graph = coverage_payload.get("dependency_graph")
    if not isinstance(dependency_graph, dict):
        return [prefix + "current public graph is missing coverage dependency graph"]
    raw_dependency_nodes = dependency_graph.get("nodes")
    if raw_dependency_nodes != b_total:
        errors.append(prefix + "current coverage dependency_graph.nodes must exactly equal B_total in order")
    raw_dependency_roots = dependency_graph.get("roots")
    if not isinstance(raw_dependency_roots, list) or any(
        not isinstance(root, str)
        or not BURDEN_ID_RE.fullmatch(root)
        or root not in b_total_set
        for root in raw_dependency_roots
    ):
        errors.append(prefix + "current coverage dependency_graph.roots must contain only B_total burden IDs")
    raw_dependency_edges = dependency_graph.get("edges")
    if not isinstance(raw_dependency_edges, list):
        errors.append(prefix + "current coverage dependency_graph.edges must be a list")
    else:
        for index, edge in enumerate(raw_dependency_edges):
            source = edge.get("from") if isinstance(edge, dict) else None
            target = edge.get("to") if isinstance(edge, dict) else None
            if (
                not isinstance(source, str)
                or not BURDEN_ID_RE.fullmatch(source)
                or source not in b_total_set
                or not isinstance(target, str)
                or not BURDEN_ID_RE.fullmatch(target)
                or target not in b_total_set
            ):
                errors.append(
                    prefix
                    + f"current coverage dependency_graph.edges[{index}] endpoints must be B_total burden IDs"
                )
    terminals = terminal_payloads(field_witness)
    nodes = set(graph_nodes(field_witness))
    raw_reread_records = field_witness.get("reread_records")
    reread_records = (
        [row for row in raw_reread_records if isinstance(row, dict)]
        if isinstance(raw_reread_records, list)
        else []
    )
    reread_burdens = [str(row.get("burden_id") or "") for row in reread_records]
    if reread_burdens != b_total:
        errors.append(prefix + "current reread_records burden order must exactly equal B_total")
    reread_cycles = [str(row.get("cycle_id") or "") for row in reread_records]
    if len(reread_cycles) != len(set(reread_cycles)):
        errors.append(prefix + "current reread_records cycle_id identities must be unique")
    raw_current_resultants = field_witness.get("mrp_resultants")
    current_resultants = (
        [row for row in raw_current_resultants if isinstance(row, dict)]
        if isinstance(raw_current_resultants, list)
        else []
    )
    resultant_pairs = [
        (str(row.get("source") or ""), str(row.get("target") or ""))
        for row in current_resultants
    ]
    if len(resultant_pairs) != len(set(resultant_pairs)):
        errors.append(prefix + "current mrp_resultants source/target identities must be unique")

    witness = parse_closure_witness(text)
    if witness is None:
        errors.append(prefix + "missing Closure/Reconstruction Witness block")
    else:
        block = extract_closure_witness_block(text) or ""
        if not B_TOTAL_LEDGER_RE.search(block):
            errors.append(prefix + "Closure/Reconstruction Witness must explicitly print B_total ledger line")
        errors.extend(prefix + error for error in closure_witness_errors(witness))
        if witness.ledger_la and witness.ledger_la != ledgers["B_LA"]:
            errors.append(prefix + "visible witness B_LA does not match current public graph B_LA")
        if witness.ledger_mrp != ledgers["B_MRP"]:
            errors.append(prefix + "visible witness B_MRP does not match current public graph B_MRP")
        if witness.ledger_total != ledgers["B_total"]:
            errors.append(prefix + "visible witness B_total does not match current public graph B_total")
        if coverage_payload.get("initial_burden_set") != witness.initial_burdens:
            errors.append(prefix + "visible initial burden set does not match current coverage initial_burden_set")
        for burden, visible_terminal in witness.terminal_states.items():
            current_terminal = terminals.get(burden)
            if current_terminal is None:
                errors.append(prefix + f"current public graph lacks visible terminal state {burden}")
            elif current_terminal.get("state") != visible_terminal.get("state"):
                errors.append(
                    prefix
                    + f"terminal state mismatch for {burden}: visible {visible_terminal.get('state')!r} "
                    + f"vs current {current_terminal.get('state')!r}"
                )
        current_edges = normalize_edges(dependency_graph.get("edges"))
        if set(current_edges) != set(witness.edges):
            errors.append(prefix + "visible dependency edges do not match current coverage dependency graph")
        if set(dependency_graph.get("roots", [])) != set(witness.roots):
            errors.append(prefix + "visible dependency roots do not match current coverage dependency graph")
        visible_divergence = status_head(witness.divergence)
        visible_curl = status_head(witness.curl)
        if status_head(str(coverage_payload.get("divergence_check") or "")) != visible_divergence:
            errors.append(prefix + "visible divergence status does not match current coverage")
        if status_head(str(coverage_payload.get("curl_check") or "")) != visible_curl:
            errors.append(prefix + "visible curl status does not match current coverage")

        visible_rereads = {
            (str(row.get("source") or ""), str(row.get("type") or ""))
            for row in witness.mrp_resultants
        }
        current_rereads = {
            (str(row.get("burden_id") or ""), str(row.get("route_result_type") or ""))
            for row in reread_records
        }
        if visible_rereads != current_rereads:
            errors.append(prefix + "visible MRP/reread rows do not match current reread_records")
        for row in current_resultants:
            identity = (
                str(row.get("source") or ""),
                str(row.get("type") or ""),
                str(row.get("route") or ""),
            )
            if not any(
                (
                    str(visible.get("source") or ""),
                    str(visible.get("type") or ""),
                    str(visible.get("route") or ""),
                )
                == identity
                for visible in witness.mrp_resultants
            ):
                errors.append(prefix + f"current edge-producing resultant {identity!r} lacks a visible MRP row")
            if (str(row.get("source") or ""), str(row.get("target") or "")) not in set(current_edges):
                errors.append(prefix + "current edge-producing resultant target is absent from dependency graph")

    layer = layer_a_obligations(text)
    if not layer["initial"]:
        errors.append(prefix + "Layer A Initial burden set missing or unparsable")
    if layer["B_LA"] and layer["B_LA"] != ledgers["B_LA"]:
        errors.append(prefix + "Layer A B_LA does not match current public graph B_LA")
    if layer["initial"] and layer["initial"] != ledgers["B_LA"]:
        errors.append(prefix + "Layer A Initial burden set must equal current public graph B_LA")
    for burden in layer["mentioned"]:
        if burden not in b_total_set:
            errors.append(prefix + f"Layer A obligation {burden} is omitted from current B_total")
        if burden not in nodes:
            errors.append(prefix + f"Layer A obligation {burden} is omitted from current dependency nodes")
        if burden not in terminals:
            errors.append(prefix + f"Layer A obligation {burden} lacks a current terminal state")

    root_edges = normalize_edges(field_witness.get("edges"))
    coverage_edges = normalize_edges(dependency_graph.get("edges"))
    if root_edges != coverage_edges:
        errors.append(prefix + "current public graph edges do not exactly project coverage dependency edges")

    generated_rows = [
        row for row in field_witness.get("generated_burdens", []) if isinstance(row, dict)
    ]
    generated_by_id = {str(row.get("id") or ""): row for row in generated_rows}
    for burden in ledgers["B_MRP"]:
        row = generated_by_id.get(burden)
        if row is None:
            errors.append(prefix + f"current generated burden {burden} lacks source/event identity")
            continue
        source = str(row.get("source") or "")
        if (source, burden) not in set(coverage_edges):
            errors.append(prefix + f"current generated burden {burden} source {source} lacks dependency edge")

    activations = [
        row for row in field_witness.get("owner_activations", []) if isinstance(row, dict)
    ]
    ordinals = [row.get("ordinal") for row in activations]
    if ordinals != list(range(len(activations))):
        errors.append(prefix + "current owner activation ordinals must be contiguous and ordered")
    body_refs = [str(row.get("body_ref") or "") for row in activations]
    if len(body_refs) != len(set(body_refs)):
        errors.append(prefix + "current owner activation body_ref identities must be unique")
    if any(str(row.get("burden_id") or "") not in b_total_set for row in activations):
        errors.append(prefix + "current owner activation references a burden outside B_total")

    ordering = field_witness.get("owner_activation_ordering")
    ordering_rows = ordering.get("rows") if isinstance(ordering, dict) else None
    ordering_identity = [
        (row.get("ordinal"), str(row.get("body_ref") or ""))
        for row in ordering_rows
        if isinstance(row, dict)
    ] if isinstance(ordering_rows, list) else []
    activation_identity = [(row.get("ordinal"), str(row.get("body_ref") or "")) for row in activations]
    if ordering_identity != activation_identity:
        errors.append(prefix + "current owner activation ordering rows must exactly project activations")

    nar = field_witness.get("normalized_activation_record")
    nar_rows = nar.get("per_burden") if isinstance(nar, dict) else None
    if not isinstance(nar_rows, list):
        errors.append(prefix + "current NAR per_burden rows missing")
    else:
        nar_burdens = [
            str(row.get("burden_id") or "") if isinstance(row, dict) else ""
            for row in nar_rows
        ]
        if nar_burdens != b_total:
            errors.append(prefix + "current NAR burden order must exactly equal B_total")
        nar_by_burden = {
            str(row.get("burden_id") or ""): row for row in nar_rows if isinstance(row, dict)
        }
        referenced_ordinals: list[int] = []
        terminal_objects = field_witness.get("terminal_states")
        reread_by_burden = {
            str(row.get("burden_id") or ""): row
            for row in field_witness.get("reread_records", [])
            if isinstance(row, dict)
        }
        for burden in b_total:
            row = nar_by_burden.get(burden)
            terminal = terminal_objects.get(burden) if isinstance(terminal_objects, dict) else None
            reread = reread_by_burden.get(burden)
            if row is None or not isinstance(terminal, dict) or reread is None:
                errors.append(prefix + f"current cycle/NAR join is incomplete for {burden}")
                continue
            cycle_id = str(row.get("cycle_id") or "")
            if cycle_id != terminal.get("cycle_id") or cycle_id != reread.get("cycle_id"):
                errors.append(prefix + f"current cycle identity drifts across NAR/terminal/reread for {burden}")
            raw_ordinals = row.get("activation_ordinals")
            if isinstance(raw_ordinals, list):
                for ordinal in raw_ordinals:
                    if not isinstance(ordinal, int) or ordinal < 0 or ordinal >= len(activations):
                        errors.append(prefix + f"current NAR {burden} references invalid activation ordinal {ordinal!r}")
                        continue
                    if activations[ordinal].get("burden_id") != burden:
                        errors.append(prefix + f"current NAR {burden} references another burden's activation")
                    referenced_ordinals.append(ordinal)
        if sorted(referenced_ordinals) != list(range(len(activations))):
            errors.append(prefix + "current NAR activation ordinals must partition all owner activations exactly once")

    closure = field_witness.get("closure")
    if isinstance(closure, dict):
        complete = coverage_payload.get("coverage_complete") is True
        if closure.get("closure_confirmed") is not complete:
            errors.append(prefix + "current closure_confirmed must equal coverage_complete")
        if closure.get("divergence") != coverage_payload.get("divergence_check"):
            errors.append(prefix + "current closure divergence must equal coverage divergence")
        if closure.get("curl") != coverage_payload.get("curl_check"):
            errors.append(prefix + "current closure curl must equal coverage curl")
        if complete:
            if closure.get("derived_decision") != "COMPLETE" or closure.get("remaining_open_ids"):
                errors.append(prefix + "current complete coverage requires COMPLETE with no remaining open ids")
            for burden, terminal in terminals.items():
                if terminal.get("state") not in {
                    "complete",
                    "landed",
                    "cleared",
                    "discharged-as-derivative",
                }:
                    errors.append(prefix + f"current complete coverage has open terminal {burden}")
    diagnostics = field_witness.get("field_diagnostics")
    if isinstance(diagnostics, dict):
        divergence = diagnostics.get("divergence")
        curl = diagnostics.get("curl")
        if not isinstance(divergence, dict) or divergence.get("status") != coverage_payload.get("divergence_check"):
            errors.append(prefix + "current structured divergence diagnostic must equal coverage")
        if not isinstance(curl, dict) or curl.get("status") != coverage_payload.get("curl_check"):
            errors.append(prefix + "current structured curl diagnostic must equal coverage")
    return errors


def convergence_errors(path: Path, text: str, *, compatibility: str = "historical") -> list[str]:
    errors: list[str] = []
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    if isinstance(payload, dict) and "field_witness" in payload:
        errors.append(f"{rel(path)}: field_witness payload must not be nested under a wrapper")
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return errors + [f"{rel(path)}: field_witness object missing"]

    for diagnostic in public_graph_contract_diagnostics(field_witness, compatibility=compatibility):
        errors.append(f"{rel(path)}: {diagnostic['failure_subcode']}: {diagnostic['message']}")
    if compatibility == "current":
        for diagnostic in terminal_public_order_diagnostics(text):
            errors.append(f"{rel(path)}: {diagnostic['failure_subcode']}: {diagnostic['message']}")
        errors.extend(current_public_convergence_errors(path, text, field_witness))
        return errors

    prefix = f"{rel(path)}: "
    errors.extend(prefix + error for error in field_witness_graph_errors(field_witness))
    witness = parse_closure_witness(text)
    if witness is not None:
        block = extract_closure_witness_block(text) or ""
        if not B_TOTAL_LEDGER_RE.search(block):
            errors.append(f"{rel(path)}: Closure/Reconstruction Witness must explicitly print B_total ledger line")
        errors.extend(prefix + error for error in closure_witness_errors(witness))
        errors.extend(prefix + error for error in compare_visible_to_field_witness(witness, field_witness))
    else:
        errors.append(f"{rel(path)}: missing Closure/Reconstruction Witness block")

    ledgers = field_witness_ledger(field_witness)
    terminals = terminal_payloads(field_witness)
    nodes = set(graph_nodes(field_witness))
    b_total = ledgers["B_total"]
    b_total_set = set(b_total)
    coverage_initial = [
        normalize_burden_id(str(item))
        for item in coverage(field_witness).get("initial_burden_set", [])
        if isinstance(item, str) and BURDEN_ID_RE.fullmatch(normalize_burden_id(item))
    ]

    layer = layer_a_obligations(text)
    if not layer["initial"]:
        errors.append(f"{rel(path)}: Layer A Initial burden set missing or unparsable")
    if layer["B_LA"] and ledgers["B_LA"] and layer["B_LA"] != ledgers["B_LA"]:
        errors.append(f"{rel(path)}: Layer A B_LA does not match field_witness B_LA")
    if layer["initial"] and ledgers["B_LA"] and layer["initial"] != ledgers["B_LA"]:
        errors.append(f"{rel(path)}: Layer A Initial burden set must equal field_witness B_LA")
    if coverage_initial and ledgers["B_LA"] and coverage_initial != ledgers["B_LA"]:
        errors.append(f"{rel(path)}: coverage_proof.initial_burden_set must equal field_witness B_LA")
    for burden in layer["mentioned"]:
        if burden not in b_total_set:
            errors.append(f"{rel(path)}: Layer A/register obligation {burden} is omitted from field_witness B_total")
        if nodes and burden not in nodes:
            errors.append(f"{rel(path)}: Layer A/register obligation {burden} is omitted from dependency_graph.nodes")
        if terminals and burden not in terminals:
            errors.append(f"{rel(path)}: Layer A/register obligation {burden} lacks terminal state")

    live_registers = live_register_obligations(text)
    register_coverage = register_floor_coverage(field_witness, terminals)
    errors.extend(
        diagnostic_completeness_errors(
            path,
            field_witness,
            live_registers,
            register_coverage,
            strict=diagnostic_completeness_required(field_witness, live_registers, register_coverage),
        )
    )
    for register in live_registers:
        covered = register_coverage.get(register, [])
        if covered or non_load_bearing_register_proof(text, register):
            continue
        errors.append(
            f"{rel(path)}: live register {register} lacks {REGISTER_LABELS.get(register, register)} burden-floor coverage or explicit non-load-bearing/HOLD/PARTIAL proof"
        )

    generated_sources = generated_burden_sources(field_witness)
    errors.extend(generation_depth_errors(path, field_witness, strict=depth_contract_required(path, field_witness)))
    resultants = field_witness_mrp_resultants(field_witness)
    errors.extend(
        normalized_activation_record_errors(
            path,
            field_witness,
            live_registers,
            strict=normalized_record_required(path, field_witness),
        )
    )
    for index, resultant in enumerate(resultants):
        result_type = str(resultant.get("type") or "").strip()
        if result_type in EDGE_REQUIRING_RESULTANT_TYPES and not resultant_edges(resultant):
            errors.append(
                f"{rel(path)}: MRP resultant {index} type {result_type} must expose a concrete B-id graph edge"
            )
    for source, target in resultant_graph_edges(resultants):
        if source not in b_total_set:
            errors.append(f"{rel(path)}: MRP resultant graph source {source} is omitted from field_witness B_total")
        if target not in b_total_set:
            errors.append(f"{rel(path)}: MRP resultant graph target {target} is omitted from field_witness B_total")
        if nodes and target not in nodes:
            errors.append(f"{rel(path)}: MRP resultant graph target {target} is omitted from dependency_graph.nodes")
        if terminals and target not in terminals:
            errors.append(f"{rel(path)}: MRP resultant graph target {target} lacks terminal state")

    for burden in ledgers["B_MRP"]:
        if burden in ledgers["B_LA"]:
            errors.append(f"{rel(path)}: generated burden {burden} is also listed in B_LA")
        source = generated_sources.get(burden)
        if not source:
            errors.append(f"{rel(path)}: B_MRP burden {burden} lacks generated_burdens/generated_by provenance")
            continue
        matches = [
            item
            for item in resultants
            if item.get("source") == source and item.get("type") == "generated_burden_instantiation"
        ]
        if not matches:
            errors.append(f"{rel(path)}: B_MRP burden {burden} lacks matching generated_burden_instantiation MRP({source}) resultant")
        elif not any(resultant_has_edge(item, source, burden) for item in matches):
            errors.append(f"{rel(path)}: B_MRP burden {burden} MRP({source}) resultant lacks graph edge {source}->{burden}")
    for burden in sorted(set(generated_sources) - set(ledgers["B_MRP"])):
        errors.append(f"{rel(path)}: generated_burdens lists {burden} outside B_MRP")

    root_edges = normalize_edges(field_witness.get("edges"))
    cov_graph = coverage(field_witness).get("dependency_graph")
    coverage_edges = normalize_edges(cov_graph.get("edges") if isinstance(cov_graph, dict) else [])
    if root_edges and coverage_edges and set(root_edges) != set(coverage_edges):
        errors.append(f"{rel(path)}: field_witness.edges do not match coverage_proof.dependency_graph.edges")
    for burden in root_burden_node_ids(field_witness):
        if burden not in b_total_set:
            errors.append(f"{rel(path)}: field_witness.nodes contains orphan burden node {burden} outside B_total")

    activation_targets = owner_activation_targets(field_witness)
    if any(payload.get("state") == "landed" for payload in terminals.values()) and not activation_targets:
        errors.append(f"{rel(path)}: landed terminal states require field_witness.owner_activations target evidence")
    for burden, terminal in terminals.items():
        if terminal.get("state") == "landed" and burden in b_total_set and burden not in activation_targets:
            errors.append(f"{rel(path)}: terminal landed burden {burden} lacks owner activation target evidence")

    claims_complete = complete_claimed(field_witness)
    cov = coverage(field_witness)
    if claims_complete and cov.get("coverage_complete") is False:
        errors.append(f"{rel(path)}: complete closure claim conflicts with coverage_complete=false")
    if claims_complete:
        divergence = status_head(diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del_dot_T"))
        curl = status_head(diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del_cross_T"))
        if divergence and divergence != "neutral":
            errors.append(f"{rel(path)}: complete closure claim requires neutral divergence, found {divergence!r}")
        if curl and curl not in {"null", "resolved"}:
            errors.append(f"{rel(path)}: complete closure claim requires null/resolved curl, found {curl!r}")
        for burden in b_total:
            terminal = terminals.get(burden)
            if not terminal:
                errors.append(f"{rel(path)}: complete closure claim missing terminal state for {burden}")
                continue
            state = terminal.get("state", "")
            detail = terminal.get("detail", "")
            if state in LIVE_TERMINAL_STATES:
                errors.append(f"{rel(path)}: complete closure claim cannot carry live terminal {burden}:{state}")
            elif state not in CLOSED_TERMINAL_STATES:
                errors.append(f"{rel(path)}: complete closure claim has non-closed terminal {burden}:{state}")
            if re.search(r"(?i)\b(?:unresolved|still live|remains live|unworked live)\b", detail):
                errors.append(f"{rel(path)}: complete closure claim leaves live/unresolved detail on {burden}")
    elif field_witness.get("collapse_complete") is True:
        errors.append(f"{rel(path)}: field_witness.collapse_complete=true without a complete closure proof")

    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument("--compatibility", choices=["current", "historical"], default="current", help="dialect for explicitly supplied --outputs; built-in fixtures remain labeled historical")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        current = json.loads((ROOT / "tests" / "witness-artifact-roles" / "valid" / "current-triplet" / "public-graph.json").read_text(encoding="utf-8"))
        historical = json.loads((ROOT / "tests" / "witness-artifact-roles" / "valid" / "historical-compatibility" / "legacy-public-graph.json").read_text(encoding="utf-8"))
        checks = [
            ("current public graph", public_graph_contract_diagnostics(current, compatibility="current") == []),
            ("historical adapter", public_graph_contract_diagnostics(historical, compatibility="historical") == []),
            ("historical graph rejected as current", bool(public_graph_contract_diagnostics(historical, compatibility="current"))),
        ]
        for name, passed in checks:
            print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
        ok = all(passed for _, passed in checks)
        print(f"field_witness convergence self-test: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = convergence_errors(path, read_text(path), compatibility="historical")
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = convergence_errors(path, read_text(path), compatibility="historical")
        if not found:
            errors.append(f"{rel(path)}: expected-invalid convergence fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in sorted(FORMALISM_NEUTRAL_INVALID_DIR.glob("field-*.md")):
        found = convergence_errors(path, read_text(path), compatibility="historical")
        if not found:
            errors.append(f"{rel(path)}: expected-invalid neutral convergence fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = convergence_errors(path, read_text(path), compatibility=args.compatibility)
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        if args.explain:
            print(json.dumps({"status": "fail", "checker_id": "field-witness-convergence", "compatibility": args.compatibility, "errors": errors}, sort_keys=True, ensure_ascii=False))
            return 1
        print("field_witness convergence check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.explain:
        print(json.dumps({"status": "pass", "checker_id": "field-witness-convergence", "compatibility": args.compatibility, "valid_checked": valid_checked, "invalid_checked": invalid_checked, "output_checked": output_checked}, sort_keys=True))
        return 0
    print("field_witness convergence check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    print("Built-in field-witness-convergence fixtures use the labeled historical compatibility adapter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
