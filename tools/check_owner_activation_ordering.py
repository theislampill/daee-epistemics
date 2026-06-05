#!/usr/bin/env python3
"""Check deterministic owner activation ordering/fingerprints.

This is a checker slice, not runtime policy. It reads
field_witness.owner_activations[], canonicalizes catalogue-backed owner facts,
and compares required activation fingerprints across repeated runs. Pure
emission order may vary; required activation set/count drift may not.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import extract_embedded_field_witness, extract_field_witness, field_witness_ledger
from check_mrp_generated_burden import (
    UNTRUSTED_ACTIVATION_SELF_CLAIMS,
    graph_burden_id,
    graph_normalized_text,
    graph_submove_id,
    strict_owner_family,
)
from delta_result_vocabulary import DELTA_RESULT_VOCABULARY


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "owner-activation-ordering"
PLAN_FIXTURE_ROOT = FIXTURE_ROOT / "plan-required"
ORDERING_ROLES = {"required", "parallel", "contingent", "optional_non_load_bearing", "hold_partial"}
NON_REQUIRED_ROLES = {"optional_non_load_bearing", "hold_partial"}
OWNER_ORDERING_POLICY_ID = "diagnostic-ir-pressure-owner-floor-v1"
SCIENCE_SOURCE_TOTALIZATION_PATTERNS = (
    "only-science",
    "science-only",
    "only science",
    "scientific-explanation",
    "scientific explanations",
    "scientific-authority",
    "scientific authority",
    "science-source",
)


OWNER_PRECEDENCE = {
    "FPD": 10,
    "SOURCE": 20,
    "M7": 30,
    "M9": 40,
    "DO_CHRISTIAN": 50,
    "DO_ATTRIBUTE": 55,
    "DO_SECOND_LOOP": 60,
    "M8": 70,
    "M1": 80,
    "M1-P": 85,
    "M3": 90,
    "P3": 95,
    "P7": 100,
    "P1": 110,
    "DOUBT_SKEPTICISM": 120,
    "LOOPBREAK": 130,
}


@dataclass(frozen=True)
class Activation:
    source: str
    target: str
    owner: str
    operation: str
    pressure: str
    body_ref: str
    delta: str
    land: str
    role: str
    group: str
    order_index: int

    def fingerprint_row(self) -> dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "owner": self.owner,
            "operation": self.operation,
            "pressure": self.pressure,
            "body_ref": self.body_ref,
            "delta": self.delta,
            "land": self.land,
            "role": self.role,
            "group": self.group,
        }

    def sort_key(self) -> tuple[Any, ...]:
        return (
            self.target,
            self.source,
            OWNER_PRECEDENCE.get(self.owner, 999),
            self.owner,
            self.operation,
            self.body_ref,
            self.pressure,
            self.delta,
            self.land,
            self.role,
            self.group,
        )


@dataclass
class ActivationReport:
    path: Path
    activations: list[Activation]
    required: list[Activation]
    raw_fingerprint: str
    canonical_fingerprint: str
    topology_fingerprint: str
    plan_fingerprint: str
    errors: list[str]


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


def canonical_text(value: Any) -> str:
    return re.sub(r"\s+", " ", graph_normalized_text(value).strip()).lower()


def canonical_land(value: Any) -> str:
    text = graph_normalized_text(value).strip()
    match = re.search(r"Land\((B\d+)\)", text)
    return f"Land({match.group(1)})" if match else text


def canonical_role(value: Any) -> str:
    role = str(value or "required").strip().lower().replace("-", "_")
    if role not in ORDERING_ROLES:
        return "required"
    return role


def delta_target(value: Any) -> str:
    text = canonical_text(value)
    match = re.search(r"(?:δ|delta)\s*[-_ ]?\(?\s*(b\d+)", text)
    return match.group(1).upper() if match else ""


def is_kappa_delta(value: Any) -> bool:
    text = canonical_text(value)
    return "κ" in text or "kappa" in text


def kappa_delta_has_explicit_carrier(item: dict[str, Any]) -> bool:
    fields = (
        item.get("kappa_carrier"),
        item.get("kappa_state"),
        item.get("dependency_radius"),
        item.get("reread_state_effect"),
        item.get("reread"),
        item.get("route_gradient"),
        item.get("delta_evidence"),
    )
    text = " ".join(str(value or "") for value in fields).lower()
    return bool(
        ("kappa" in text or "κ" in text)
        and ("r(h" in text or "reread" in text or "dependency" in text or "carrier" in text)
    )


def canonical_delta(value: Any, target: str) -> str:
    found_target = delta_target(value)
    resolved_target = found_target
    if not resolved_target and target and is_kappa_delta(value):
        resolved_target = target
    if not resolved_target:
        return canonical_text(value)

    text = canonical_text(value)
    target_text = resolved_target.lower()
    compact_match = re.match(r"^(?:delta|δ|Δ)\s*(?:b)?\s*\d+\s*:?\s*(?P<suffix>.*)$", text)
    if compact_match:
        suffix = compact_match.group("suffix").strip()
        return f"Delta({resolved_target}):{suffix}" if suffix else f"Delta({resolved_target})"
    kappa_match = re.match(r"^(?:delta|δ|Δ)\s*[-_ ]?\s*(?:κ|kappa)\s*:?\s*(?P<suffix>.*)$", text)
    if kappa_match:
        suffix = kappa_match.group("suffix").strip()
        return f"Delta({resolved_target}):{suffix}" if suffix else f"Delta({resolved_target})"
    prefix_patterns = [
        rf"^(?:delta|δ|Δ)\s*\(\s*{re.escape(target_text)}\s*\)\s*:?\s*",
        rf"^(?:delta|δ|Δ)\s+{re.escape(target_text)}\s*:?\s*",
        rf"^(?:delta|δ|Δ)\s*[-_ ]\s*{re.escape(target_text)}\s*:?\s*",
    ]
    suffix = text
    for pattern in prefix_patterns:
        stripped = re.sub(pattern, "", text, count=1)
        if stripped != text:
            suffix = stripped
            break
    if suffix and suffix != text:
        return f"Delta({resolved_target}):{suffix}"
    return f"Delta({resolved_target})"


def delta_result_suffix(delta: str) -> str:
    if ":" not in delta:
        return ""
    return canonical_text(delta.split(":", 1)[1])


def delta_result_vocabulary_errors(label: str, owner: str, delta: str) -> list[str]:
    vocabulary = DELTA_RESULT_VOCABULARY.get(owner)
    if vocabulary is None:
        return []
    suffix = delta_result_suffix(delta)
    if not suffix:
        return [f"{label}: delta must include owner-local delta_result token for {owner}"]
    if suffix not in vocabulary:
        allowed = ", ".join(sorted(vocabulary))
        return [
            f"{label}: delta_result token {suffix!r} is outside controlled vocabulary "
            f"for {owner}; allowed: {allowed}"
        ]
    return []


def source_recoil_delta_errors(label: str, owner: str, pressure: str, delta: str) -> list[str]:
    if owner != "SOURCE":
        return []
    pressure_key = canonical_text(pressure)
    has_hidden_support = (
        "hidden-support" in pressure_key
        or ("hidden" in pressure_key and "support" in pressure_key)
    )
    has_source_recoil = any(token in pressure_key for token in ("recoil", "future-support"))
    if not (has_hidden_support or has_source_recoil):
        return []
    suffix = delta_result_suffix(delta)
    is_proof_text_hidden_support = has_hidden_support and any(
        token in pressure_key for token in ("proof-text", "proof-stack", "backread")
    )
    if is_proof_text_hidden_support:
        if suffix == "proof-text-hidden-support-blocked":
            return []
        return [
            f"{label}: proof-text/proof-stack hidden-support pressure must use "
            "delta_result token 'proof-text-hidden-support-blocked'"
        ]
    if suffix == "hidden-support-blocked":
        return []
    return [
        f"{label}: source-order recoil or hidden-support pressure must use "
        "delta_result token 'hidden-support-blocked'"
    ]


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def normalize_activation(
    path: Path,
    item: dict[str, Any],
    index: int,
    *,
    require_plan: bool = False,
) -> tuple[Activation | None, list[str]]:
    label = f"{rel(path)}: owner_activations[{index}]"
    errors: list[str] = []
    self_claims = sorted(UNTRUSTED_ACTIVATION_SELF_CLAIMS.intersection(item))
    if self_claims:
        errors.append(
            f"{label}: model-authored activation verification fields are not proof: "
            + ", ".join(self_claims)
        )

    owner_raw = str(item.get("owner") or "").strip()
    owner = strict_owner_family(owner_raw)
    if not owner:
        errors.append(f"{label}: owner {owner_raw!r} is not catalogue-backed")
        owner = owner_raw.upper()

    source = graph_burden_id(item.get("source"))
    target = graph_burden_id(item.get("target"))
    body_ref = graph_submove_id(item.get("body_ref"))
    operation = canonical_text(item.get("operation"))
    pressure = canonical_text(item.get("pressure"))
    raw_delta = item.get("delta")
    delta = canonical_delta(raw_delta, target)
    land = canonical_land(item.get("land"))
    role_value = item.get("ordering_role") or item.get("role")
    role = canonical_role(role_value)
    group = canonical_text(item.get("ordering_group") or item.get("parallel_group") or "")
    if require_plan and role_value is None:
        errors.append(f"{label}: deterministic plan requires explicit ordering_role")

    required_fields = {
        "source": source,
        "target": target,
        "owner": owner_raw,
        "operation": operation,
        "pressure": pressure,
        "body_ref": body_ref,
        "delta": delta,
        "land": land,
    }
    missing = sorted(key for key, value in required_fields.items() if not str(value).strip())
    if missing:
        errors.append(f"{label}: missing required activation fields: {', '.join(missing)}")
    if role == "contingent" and not canonical_text(item.get("trigger")):
        errors.append(f"{label}: contingent owner activation requires trigger")
    if role in {"parallel", "optional_non_load_bearing"} and not group:
        errors.append(f"{label}: {role} owner activation requires ordering_group")
    if target and body_ref and not body_ref.startswith(f"{target}_"):
        errors.append(f"{label}: body_ref {body_ref!r} does not belong to target {target}")
    found_delta_target = delta_target(raw_delta)
    if target and found_delta_target and found_delta_target != target:
        errors.append(f"{label}: delta target {found_delta_target} does not match activation target {target}")
    elif target and not found_delta_target:
        if is_kappa_delta(raw_delta):
            if not kappa_delta_has_explicit_carrier(item):
                errors.append(
                    f"{label}: Delta-kappa without raw burden target requires explicit "
                    "kappa carrier/dependency-radius/R(H,Delta) evidence"
                )
        else:
            errors.append(f"{label}: delta must name activation target {target} or use Delta-kappa")
    errors.extend(delta_result_vocabulary_errors(label, owner, delta))
    errors.extend(source_recoil_delta_errors(label, owner, pressure, delta))

    if missing:
        return None, errors
    return (
        Activation(
            source=source,
            target=target,
            owner=owner,
            operation=operation,
            pressure=pressure,
            body_ref=body_ref,
            delta=delta,
            land=land,
            role=role,
            group=group,
            order_index=index,
        ),
        errors,
    )


def ordering_surface(field_witness: dict[str, Any]) -> Any:
    raw = field_witness.get("owner_activation_ordering")
    return raw


def ordering_rules(field_witness: dict[str, Any]) -> list[dict[str, Any]]:
    raw = ordering_surface(field_witness)
    if isinstance(raw, dict):
        raw = raw.get("required_before") or raw.get("rules") or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def closure_status_value(field_witness: dict[str, Any]) -> str:
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness.get("coverage_proof"), dict) else {}
    if "coverage_complete" in coverage:
        return str(coverage.get("coverage_complete")).strip().lower()
    closure = field_witness.get("closure") if isinstance(field_witness.get("closure"), dict) else {}
    if "coverage_complete" in closure:
        return str(closure.get("coverage_complete")).strip().lower()
    status = canonical_text(closure.get("status")) if closure else ""
    match = re.search(r"coverage_complete\s*[:=]\s*(true|false)", status)
    if match:
        return match.group(1)
    return ""


def topology_fingerprint(field_witness: dict[str, Any]) -> str:
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness.get("coverage_proof"), dict) else {}
    graph = coverage.get("dependency_graph") if isinstance(coverage.get("dependency_graph"), dict) else {}
    ledgers = field_witness_ledger(field_witness)
    terminals = coverage.get("terminal_states")
    if not isinstance(terminals, dict):
        terminals = field_witness.get("terminal_states") if isinstance(field_witness.get("terminal_states"), dict) else {}
    return digest(
        {
            "B_LA": ledgers["B_LA"],
            "B_MRP": ledgers["B_MRP"],
            "B_total": ledgers["B_total"],
            "coverage_complete": closure_status_value(field_witness),
            "edges": graph.get("edges") or field_witness.get("edges") or [],
            "terminals": terminals,
        }
    )


def normalized_owner(value: Any) -> str:
    raw = str(value or "").strip()
    return strict_owner_family(raw) or canonical_text(raw).upper()


def ordering_plan_fingerprint(field_witness: dict[str, Any]) -> str:
    raw = ordering_surface(field_witness)
    if not isinstance(raw, dict):
        return ""

    required_before_rows = []
    for item in raw.get("required_before") or raw.get("rules") or []:
        if not isinstance(item, dict):
            continue
        required_before_rows.append(
            {
                "target": graph_burden_id(item.get("target")),
                "before_owner": normalized_owner(item.get("before_owner")),
                "after_owner": normalized_owner(item.get("after_owner")),
            }
        )
    required_before_rows = sorted(
        required_before_rows,
        key=lambda row: (row["target"], row["before_owner"], row["after_owner"]),
    )

    parallel_group_rows = []
    for item in raw.get("parallel_groups") or []:
        if not isinstance(item, dict):
            continue
        owners = sorted({normalized_owner(owner) for owner in item.get("owners") or [] if normalized_owner(owner)})
        parallel_group_rows.append(
            {
                "target": graph_burden_id(item.get("target")),
                "group": canonical_text(item.get("group")),
                "owners": owners,
            }
        )
    parallel_group_rows = sorted(
        parallel_group_rows,
        key=lambda row: (row["target"], row["group"], ",".join(row["owners"])),
    )

    return digest(
        {
            "policy_id": raw.get("policy_id"),
            "required_before": required_before_rows,
            "parallel_groups": parallel_group_rows,
        }
    )


def activation_report(path: Path, *, require_plan: bool = False) -> ActivationReport:
    text = read_text(path)
    field_witness, errors = parse_field_witness(path, text)
    activations: list[Activation] = []
    if field_witness is None:
        return ActivationReport(path, [], [], "", "", "", "", errors)
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return ActivationReport(
            path,
            [],
            [],
            "",
            "",
            topology_fingerprint(field_witness),
            ordering_plan_fingerprint(field_witness),
            errors + [f"{rel(path)}: field_witness.owner_activations must be a list"],
        )
    if require_plan:
        raw_ordering = ordering_surface(field_witness)
        if not isinstance(raw_ordering, dict):
            errors.append(
                f"{rel(path)}: deterministic plan requires field_witness.owner_activation_ordering "
                "as an object"
            )
        elif raw_ordering.get("policy_id") != OWNER_ORDERING_POLICY_ID:
            errors.append(
                f"{rel(path)}: deterministic plan requires owner_activation_ordering.policy_id="
                f"{OWNER_ORDERING_POLICY_ID!r}"
            )
        if isinstance(raw_ordering, dict) and "policy" in raw_ordering:
            errors.append(
                f"{rel(path)}: owner_activation_ordering.policy is not valid; use only "
                "owner_activation_ordering.policy_id"
            )

    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            errors.append(f"{rel(path)}: owner_activations[{index}] must be a JSON object")
            continue
        activation, found = normalize_activation(path, item, index, require_plan=require_plan)
        errors.extend(found)
        if activation is not None:
            activations.append(activation)

    rows = [activation.fingerprint_row() for activation in activations]
    required = [activation for activation in activations if activation.role not in NON_REQUIRED_ROLES]
    sorted_required = sorted(required, key=lambda activation: activation.sort_key())
    canonical_rows = [activation.fingerprint_row() for activation in sorted_required]
    duplicates = sorted(
        {
            digest(row)
            for row in canonical_rows
            if canonical_rows.count(row) > 1
        }
    )
    if duplicates:
        errors.append(f"{rel(path)}: duplicate required owner activation rows in canonical plan")

    rules = ordering_rules(field_witness)
    errors.extend(required_before_errors(path, activations, rules))
    errors.extend(science_source_gate_errors(path, activations, rules))
    if require_plan:
        errors.extend(plan_surface_errors(path, activations, rules))
        errors.extend(parallel_group_errors(path, field_witness, activations))

    return ActivationReport(
        path=path,
        activations=activations,
        required=required,
        raw_fingerprint=digest(rows) if rows else "",
        canonical_fingerprint=digest(canonical_rows) if canonical_rows else "",
        topology_fingerprint=topology_fingerprint(field_witness),
        plan_fingerprint=ordering_plan_fingerprint(field_witness),
        errors=errors,
    )


def required_before_errors(path: Path, activations: list[Activation], rules: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not rules:
        return errors
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            errors.append(
                f"{rel(path)}: owner_activation_ordering.required_before[{index}] must be an object "
                "with target, before_owner, and after_owner"
            )
            continue
        target = graph_burden_id(rule.get("target"))
        before_owner = strict_owner_family(str(rule.get("before_owner") or rule.get("before") or ""))
        after_owner = strict_owner_family(str(rule.get("after_owner") or rule.get("after") or ""))
        if not target or not before_owner or not after_owner:
            errors.append(f"{rel(path)}: owner_activation_ordering.required_before[{index}] is incomplete")
            continue
        target_activations = [
            activation for activation in activations if activation.target == target and activation.role not in NON_REQUIRED_ROLES
        ]
        before_positions = [activation.order_index for activation in target_activations if activation.owner == before_owner]
        after_positions = [activation.order_index for activation in target_activations if activation.owner == after_owner]
        if not before_positions or not after_positions:
            errors.append(
                f"{rel(path)}: owner_activation_ordering.required_before[{index}] references missing owners for {target}"
            )
            continue
        if min(before_positions) > min(after_positions):
            errors.append(
                f"{rel(path)}: owner_activation_ordering.required_before[{index}] violated for {target}: "
                f"{before_owner} must precede {after_owner}"
            )
    return errors


def plan_surface_errors(path: Path, activations: list[Activation], rules: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_target: dict[str, list[Activation]] = {}
    for activation in activations:
        by_target.setdefault(activation.target, []).append(activation)

    rule_targets = {graph_burden_id(rule.get("target")) for rule in rules if isinstance(rule, dict)}
    for target, target_activations in sorted(by_target.items()):
        load_bearing = [activation for activation in target_activations if activation.role not in NON_REQUIRED_ROLES]
        if len(load_bearing) <= 1:
            continue
        all_parallel = all(activation.role == "parallel" and activation.group for activation in load_bearing)
        has_required_before = target in rule_targets
        if not all_parallel and not has_required_before:
            errors.append(
                f"{rel(path)}: target {target} has multiple load-bearing owner activations but no "
                "deterministic required_before rule or parallel ordering group"
            )
    return errors


def science_source_gate_errors(path: Path, activations: list[Activation], rules: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_target: dict[str, list[Activation]] = {}
    for activation in activations:
        if activation.role not in NON_REQUIRED_ROLES:
            by_target.setdefault(activation.target, []).append(activation)

    before_after = {
        (
            graph_burden_id(rule.get("target")),
            strict_owner_family(str(rule.get("before_owner") or rule.get("before") or "")),
            strict_owner_family(str(rule.get("after_owner") or rule.get("after") or "")),
        )
        for rule in rules
        if isinstance(rule, dict)
    }

    for target, target_activations in sorted(by_target.items()):
        m1_activations = [activation for activation in target_activations if activation.owner == "M1"]
        if not m1_activations:
            continue
        science_m1 = [
            activation
            for activation in m1_activations
            if any(
                pattern
                in " ".join(
                    [
                        activation.pressure,
                        activation.operation,
                        activation.delta,
                    ]
                )
                for pattern in SCIENCE_SOURCE_TOTALIZATION_PATTERNS
            )
        ]
        if not science_m1:
            continue
        source_activations = [activation for activation in target_activations if activation.owner == "SOURCE"]
        if not source_activations:
            errors.append(
                f"{rel(path)}: target {target} has science-only/source-order M1 pressure but no "
                "source-status-repair or authority-order source gate activation"
            )
            continue
        if (target, "SOURCE", "M1") not in before_after:
            errors.append(
                f"{rel(path)}: target {target} has science-only/source-order pressure but no "
                "required_before edge from source-status-repair/SOURCE to M1"
            )
    return errors


def parallel_group_errors(path: Path, field_witness: dict[str, Any], activations: list[Activation]) -> list[str]:
    raw = ordering_surface(field_witness)
    if not isinstance(raw, dict):
        return []
    plan_groups: dict[tuple[str, str], set[str]] = {}
    errors: list[str] = []
    for index, item in enumerate(raw.get("parallel_groups") or [], start=1):
        if not isinstance(item, dict):
            errors.append(f"{rel(path)}: owner_activation_ordering.parallel_groups[{index}] must be an object")
            continue
        target = graph_burden_id(item.get("target"))
        group = canonical_text(item.get("group"))
        owners = {normalized_owner(owner) for owner in item.get("owners") or [] if normalized_owner(owner)}
        if not target or not group or len(owners) < 2:
            errors.append(f"{rel(path)}: owner_activation_ordering.parallel_groups[{index}] is incomplete")
            continue
        plan_groups[(target, group)] = owners

    activation_groups: dict[tuple[str, str], set[str]] = {}
    for activation in activations:
        if activation.role == "parallel":
            activation_groups.setdefault((activation.target, activation.group), set()).add(activation.owner)

    for key, owners in sorted(activation_groups.items()):
        target, group = key
        planned = plan_groups.get(key)
        if planned is None:
            errors.append(
                f"{rel(path)}: parallel owner activations for {target}/{group} have no matching "
                "owner_activation_ordering.parallel_groups entry"
            )
        elif planned != owners:
            errors.append(
                f"{rel(path)}: parallel owner group {target}/{group} disagrees with activations: "
                f"plan={sorted(planned)} activations={sorted(owners)}"
            )
    return errors


def compare_reports(reports: list[ActivationReport]) -> list[str]:
    errors: list[str] = []
    if len(reports) < 2:
        return ["compare-runs requires at least two outputs"]
    for report in reports:
        errors.extend(report.errors)
    if errors:
        return errors

    topology = {report.topology_fingerprint for report in reports}
    if len(topology) != 1:
        errors.append(
            "repeated-run coarse graph/topology fingerprints differ: "
            + ", ".join(f"{rel(report.path)}={report.topology_fingerprint[:12]}" for report in reports)
        )
    canonical = {report.canonical_fingerprint for report in reports}
    if len(canonical) != 1:
        errors.append(
            "repeated-run canonical required owner activation fingerprints differ: "
            + ", ".join(
                f"{rel(report.path)}={report.canonical_fingerprint[:12]} count={len(report.required)}"
                for report in reports
            )
        )
    plan = {report.plan_fingerprint for report in reports if report.plan_fingerprint}
    if len(plan) > 1:
        errors.append(
            "repeated-run owner activation ordering plans differ: "
            + ", ".join(f"{rel(report.path)}={report.plan_fingerprint[:12]}" for report in reports)
        )
    return errors


def group_dirs(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(path for path in base.iterdir() if path.is_dir())


def direct_fixtures(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(path for path in base.glob("*.md"))


def run_fixture_suite(root: Path, *, require_plan: bool = False) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    if not root.exists():
        return errors, valid_checked, invalid_checked

    for path in direct_fixtures(root, "valid"):
        report = activation_report(path, require_plan=require_plan)
        if report.errors:
            errors.extend(report.errors)
        else:
            valid_checked += 1
    for path in direct_fixtures(root, "invalid"):
        report = activation_report(path, require_plan=require_plan)
        if not report.errors:
            errors.append(f"{rel(path)}: expected-invalid owner activation fixture unexpectedly passed")
        else:
            invalid_checked += 1

    for directory in group_dirs(root, "valid"):
        reports = [activation_report(path, require_plan=require_plan) for path in sorted(directory.glob("*.md"))]
        found = compare_reports(reports)
        if found:
            errors.extend(f"{rel(directory)}: {error}" for error in found)
        else:
            valid_checked += 1
    for directory in group_dirs(root, "invalid"):
        reports = [activation_report(path, require_plan=require_plan) for path in sorted(directory.glob("*.md"))]
        found = compare_reports(reports)
        if not found:
            errors.append(f"{rel(directory)}: expected-invalid owner activation group unexpectedly passed")
        else:
            invalid_checked += 1
    return errors, valid_checked, invalid_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument("--compare-runs", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--require-plan",
        action="store_true",
        help="Require explicit deterministic owner activation ordering metadata on outputs.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    root_requires_plan = args.require_plan and args.root.resolve() != FIXTURE_ROOT.resolve()
    suite_errors, valid_checked, invalid_checked = run_fixture_suite(args.root, require_plan=root_requires_plan)
    errors.extend(suite_errors)
    if args.root.resolve() == FIXTURE_ROOT.resolve():
        plan_errors, plan_valid, plan_invalid = run_fixture_suite(PLAN_FIXTURE_ROOT, require_plan=True)
        errors.extend(plan_errors)
        valid_checked += plan_valid
        invalid_checked += plan_invalid

    for path in expand_paths(args.outputs):
        report = activation_report(path, require_plan=args.require_plan)
        if report.errors:
            errors.extend(report.errors)
        else:
            output_checked += 1

    compared = 0
    if args.compare_runs:
        reports = [activation_report(path, require_plan=args.require_plan) for path in expand_paths(args.compare_runs)]
        errors.extend(compare_reports(reports))
        if not errors:
            compared = len(reports)

    if errors:
        print("owner activation ordering check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("owner activation ordering check: PASS")
    print(f"Valid fixtures/groups checked: {valid_checked}")
    print(f"Invalid fixtures/groups checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    if args.compare_runs:
        print(f"Compared repeated-run outputs: {compared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
