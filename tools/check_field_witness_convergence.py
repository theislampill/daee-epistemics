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
    status_head,
    unique,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "field-witness-convergence"

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
        if any(keyword in lowered for keyword in keywords) and register not in found:
            found.append(register)
    return found


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
    explicit = explicit_node_registers(node)
    if explicit:
        return explicit
    parts: list[str] = []
    for key in ("title", "label", "pressure", "register_operation", "operation", "finding", "type"):
        value = node.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    if terminal:
        parts.append(terminal.get("detail", ""))
        parts.append(terminal.get("state", ""))
    text = " ".join(parts).lower()
    return [
        register
        for register, keywords in REGISTER_BURDEN_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]


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
    try:
        if path.resolve().is_relative_to(FIXTURE_ROOT.resolve()):
            return True
    except AttributeError:
        try:
            path.resolve().relative_to(FIXTURE_ROOT.resolve())
            return True
        except ValueError:
            pass
    cov = coverage(field_witness)
    if "max_generation_depth" in cov:
        return True
    return any(record.get("has_depth") for record in generated_burden_records(field_witness).values())


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
    valid_root = FIXTURE_ROOT / "valid"
    try:
        if path.resolve().is_relative_to(valid_root.resolve()):
            return True
    except AttributeError:
        try:
            path.resolve().relative_to(valid_root.resolve())
            return True
        except ValueError:
            pass
    return "normalized_activation_record" in field_witness


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


def convergence_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    if isinstance(payload, dict) and "field_witness" in payload:
        errors.append(f"{rel(path)}: field_witness payload must not be nested under a wrapper")
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return errors + [f"{rel(path)}: field_witness object missing"]

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
            strict=path.resolve().is_relative_to(FIXTURE_ROOT.resolve()) if hasattr(Path, "is_relative_to") else False,
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
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = convergence_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = convergence_errors(path, read_text(path))
        if not found:
            errors.append(f"{rel(path)}: expected-invalid convergence fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = convergence_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("field_witness convergence check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("field_witness convergence check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
