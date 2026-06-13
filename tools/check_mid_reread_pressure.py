#!/usr/bin/env python3
"""Validate Mid-Reread Pressure (TTP-MRP) fixtures.

The checker is intentionally structural. It validates the compact
`[Mid-Reread Pressure]` block, route/graph consequences, non-claim boundaries,
and optional `field_witness.reread_pressure` sidecar evidence without grading
the philosophical quality of the answer.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    closure_witness_errors,
    compare_visible_to_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    load_json,
    parse_closure_witness,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


FINDINGS = {
    "stable",
    "genuine-dependent",
    "partial-real",
    "hidden-framework-recoil",
    "doubt-churn",
    "reorientation",
}
ROUTES = {"STOP", "HOLD", "RECURSE", "LoopBreak(∇×T)"}
ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
PRESSURE_KEYS = {
    "freeze-landed-move",
    "dependency-tug",
    "hidden-framework-recoil",
    "entailment-pressure",
    "doubt-churn-guard",
    "reorientation-reminder",
}
ALLOWED_DIVERGENCE = {"neutral", "settled", "bounded", "non-neutral"}
ALLOWED_CURL = {"null", "resolved", "held", "non-null"}
REREAD_RE = re.compile(r"R\(H,\s*(?:Delta|Δ)\)")
LANDED_DELTA_RE = re.compile(r"(?:Delta|Δ|ΔⁿB)")
DIRECT_REREAD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?`?R\(H,\s*(?:Delta|Δ)\)`?\s*:\s*(?:\*\*)?\s*(?P<body>\S.*)$"
)
BARE_DIRECT_REREAD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?`?R\(H,\s*(?:Delta|Δ)\)`?\s*:\s*(?:\*\*)?\s*$"
)
FIELD_DIAGNOSTICS_DIVERGENCE_RE = re.compile(
    r"(?:∇\s*·\s*B|del[- ]dot\s*B)\s*:\s*(?P<body>[^;\n]+)",
    re.IGNORECASE,
)
FIELD_DIAGNOSTICS_CURL_RE = re.compile(
    r"(?:∇\s*×\s*(?:κ|kappa)|del[- ]cross\s*(?:κ|kappa))\s*:\s*(?P<body>[^;\n]+)",
    re.IGNORECASE,
)
MRP_HEADING_RE = (
    r"^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?(?:\*\*)?\[Mid-Reread Pressure\](?:\*\*)?\s*$"
)
MRP_BLOCK_RE = re.compile(
    r"(?ims)" + MRP_HEADING_RE + r"\s*(?P<body>.*?)(?="
    + MRP_HEADING_RE
    + r"|^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+\b|Closure/Reconstruction Witness\b|"
    r"Closure Audit\b|Restorative Response\b|Closing Formulation\b)|\Z)"
)
LAND_GATE_RE = re.compile(r"(?m)^Land\((?P<burden>[¹²³⁴⁵⁶⁷⁸⁹]B)\):")
STOP_ROUTE_RE = re.compile(r"(?im)^\s*Route\s*:\s*STOP\b")
POST_STOP_CONTINUATION_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+\b|Layer B\b|.*Layer B\s*[-—]\s*Governed Operation Body\b)"
)
POST_STOP_TERMINAL_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:Closure/Reconstruction Witness\b|Restorative Response\b|Closing Formulation\b)"
)
LINEAR_DEPENDENCY_RE = re.compile(
    r"(?i)\b(?:depends on|downstream|directed dependency|linear(?:ly)? traversable|"
    r"B\d+\s*(?:->|→)\s*B\d+|remaining live burden)\b"
)
CURL_REASON_RE = re.compile(
    r"(?i)\b(?:loop|circular|rotation|rotational|rotated|churn|recoil|label-pressure|"
    r"self-reinforcing|regress|wisw[āa]s|framework)\b"
)
STRICT_CURL_REASON_RE = re.compile(
    r"(?i)\b(?:circular|rotation|rotational|rotated|churn|recoil|label-pressure|"
    r"self-reinforcing|regress|wisw[āa]s)\b"
)
CURL_NEGATION_RE = re.compile(r"(?i)\b(?:no loop|no circular|no churn|not a loop|not circular)\b")

ACTIVATION_OWNER_RE = re.compile(
    r"\b(?:[A-Za-z0-9]+-[A-Za-z0-9-]+|diagnostic-render-contract|closure witness graph|"
    r"field_witness|pressure class|terminal-state|foreign-premise|definition|grief|"
    r"FPD|M\d+|M1P|V\d+|R\d+|P\d+|LoopBreak|doubt-vs-skepticism|"
    r"source-architecture|predicate discipline|application hold|hujjah|hiddenness|"
    r"coercive-guidance|closure-witness|coverage gap)\b"
)
BURDEN_ARROW_TARGET_RE = re.compile(
    r"(?:"
    r"(?:->|→)\s*(?:B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\b|"
    r"(?:B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s+(?:pressure\s+highest|released|remains\s+live)"
    r")",
    re.IGNORECASE,
)
MRP_REFUTATION_BODY_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:Operation|Result|Contribution-to-Land)\s*:"
)
HIGH_LEVERAGE_ROUTE_RE = re.compile(
    r"(?i)\b(?:independent lordship|canon(?:[- ]wide)?|canon/source authority|"
    r"source authority|source[- ]order inversion|textual criticism|source-authentication|"
    r"proof[- ]stack|moral tribunal|worldview recoil|source[- ]worldview|"
    r"identity/worldview|predication|category repair|hiddenness|coercive guidance|"
    r"guidance|shubha|shakk|rayb|authority[- ]order|transmission|criterion|"
    r"translation tribunal|admissibility tribunal|burden-gradient|dependency radius)\b"
)
DOUBT_CHURN_PROOF_STACK_RE = re.compile(
    r"(?i)\b(?:more proof|another proof|proof-stack|proof stack|additional evidence dump|"
    r"adding proof after proof|stacking another proof)\b"
)
ANTI_PROOF_STACKING_CONTEXT_RE = re.compile(
    r"(?i)\b(?:not|no|without|refus(?:e|es|ed|ing)|will not|won't|do not|does not|"
    r"cannot|can't|must not|blocked|stop(?:s|ped|ping)?|non[-_ ]claims?|"
    r"held non-claim|rather than|instead of)\b"
)
HELD_OR_UNWORKED_ROUTE_RE = re.compile(
    r"(?i)\b(?:held beyond prompt|held beyond|beyond prompt|beyond bounded claim|"
    r"held outside scope|outside scope|not released|unreleased|not worked|unworked|"
    r"not executed|not discharged|left held|carried outside)\b"
)
HELD_ROUTE_LICENSE_RE = re.compile(
    r"(?i)\b(?:HOLD|PARTIAL|RECURSE|generated_burden_instantiation|"
    r"held_burden_activation|non[- ]load[- ]bearing|not load[- ]bearing|"
    r"not needed for (?:this|the) (?:scoped|bounded|local) claim|"
    r"scope gate|local closure only|partial closure|coverage_complete\s*=\s*false|"
    r"explicitly held with reason|held-with-reason)\b"
)
COMPLETE_CLOSURE_STATUS_RE = re.compile(
    r"(?i)\b(?:COMPLETE|complete closure|coverage_complete\s*[:=]\s*true|"
    r"runtime .*closed|execution field closed|collapse achieved|no remaining live problem)\b"
)


@dataclass
class MrpBlock:
    body: str
    target: str
    reread: str
    landed_delta: str
    route_gradient: str
    divergence: str
    curl: str
    finding: str
    route_result_type: str
    mrp_resultant: str
    graph_delta: str
    preemption_basis: str
    route: str
    boundary: str
    pressure_lines: dict[str, str]


def extract_block(text: str) -> str:
    match = MRP_BLOCK_RE.search(text)
    return match.group("body").strip() if match else ""


def extract_blocks(text: str) -> list[str]:
    return [match.group("body").strip() for match in MRP_BLOCK_RE.finditer(text)]


def field(body: str, name: str) -> str:
    match = re.search(
        rf"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(name)}\s*:\s*(?:\*\*)?\s*(?P<body>.+)$",
        body,
    )
    return match.group("body").strip() if match else ""


def field_any(body: str, names: tuple[str, ...]) -> str:
    for name in names:
        found = field(body, name)
        if found:
            return found
    return ""


def direct_reread(body: str) -> str:
    match = DIRECT_REREAD_RE.search(body)
    if not match:
        return ""
    return f"R(H,Δ): {match.group('body').strip()}"


def field_diagnostic_value(body: str, pattern: re.Pattern[str]) -> str:
    diagnostics = field(body, "Field diagnostics")
    if not diagnostics:
        return ""
    match = pattern.search(diagnostics)
    if not match:
        return ""
    return match.group("body").strip()


def parse_pressure_lines(body: str) -> dict[str, str]:
    pressure: dict[str, str] = {}
    for key in PRESSURE_KEYS:
        match = re.search(
            rf"(?im)^\s*[-*]\s*(?:\*\*)?{re.escape(key)}\s*:\s*(?:\*\*)?\s*(?P<body>.+)$",
            body,
        )
        if match:
            pressure[key] = match.group("body").strip()
    return pressure


def parse_mrp(text: str) -> MrpBlock | None:
    body = extract_block(text)
    if not body:
        return None
    return parse_mrp_body(body)


def parse_mrp_body(body: str) -> MrpBlock:
    return MrpBlock(
        body=body,
        target=field(body, "Target"),
        reread=field(body, "Reread") or direct_reread(body),
        landed_delta=field(body, "Landed delta"),
        route_gradient=field(body, "Route-gradient"),
        divergence=field_any(body, ("∇·T", "∇·B", "del-dot T", "del dot T", "del-dot-T", "del-dot B"))
        or field_diagnostic_value(body, FIELD_DIAGNOSTICS_DIVERGENCE_RE),
        curl=field_any(body, ("∇×T", "∇×κ", "del-cross T", "del cross T", "del-cross-T", "del-cross kappa"))
        or field_diagnostic_value(body, FIELD_DIAGNOSTICS_CURL_RE),
        finding=field(body, "Finding"),
        route_result_type=field(body, "MRP route result type"),
        mrp_resultant=field(body, "MRP resultant"),
        graph_delta=field(body, "Graph delta"),
        preemption_basis=field(body, "Pre-emption basis"),
        route=field(body, "Route"),
        boundary=field(body, "Boundary"),
        pressure_lines=parse_pressure_lines(body),
    )


def parse_mrps(text: str) -> list[MrpBlock]:
    return [parse_mrp_body(body) for body in extract_blocks(text)]


def sidecar_path_for(path: Path) -> Path:
    return path.with_name(path.stem + ".field_witness.json")


def load_sidecar(path: Path) -> dict[str, Any] | None:
    sidecar = sidecar_path_for(path)
    if not sidecar.is_file():
        return None
    return extract_field_witness(load_json(sidecar))


def has_edge(value: str) -> bool:
    return bool(re.search(r"(?:→|->)", value))


def edge_targets(value: str) -> set[str]:
    return {
        match.group("dst")
        for match in re.finditer(
            r"(?P<src>(?:B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B))\s*(?:→|->)\s*(?P<dst>(?:B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B))",
            value,
        )
    }


def is_none_delta(value: str) -> bool:
    return bool(re.search(r"(?i)\b(?:none|no new graph edge|no-edge)\b", value))


def activation_names_owner_or_gap(value: str) -> bool:
    return bool(ACTIVATION_OWNER_RE.search(value))


def first_state(value: str) -> str:
    normalized = value.strip().lower()
    for allowed in sorted(ALLOWED_DIVERGENCE | ALLOWED_CURL, key=len, reverse=True):
        if re.match(rf"^{re.escape(allowed)}(?:\b|/|;|\s)", normalized):
            return allowed
    return re.split(r"\s*/\s*|\s+-\s+|\s+—\s+|\s*;\s*", value.strip(), maxsplit=1)[0].strip().lower()


def has_positive_proof_stacking_after_doubt_churn(text: str) -> bool:
    for match in DOUBT_CHURN_PROOF_STACK_RE.finditer(text):
        window_start = text.rfind("\n", 0, match.start()) + 1
        window_end = text.find("\n", match.end())
        if window_end == -1:
            window_end = len(text)
        window = text[window_start:window_end]
        if ANTI_PROOF_STACKING_CONTEXT_RE.search(window):
            continue
        return True
    return False


def mrp_refutation_content_errors(mrp: MrpBlock, label: str) -> list[str]:
    if MRP_REFUTATION_BODY_RE.search(mrp.body):
        return [
            f"{label}: MRP contains refutation/preemption prose content. This work belongs in the Layer B of the generated B, not in the MRP block."
        ]
    return []


def direct_reread_content_errors(mrp: MrpBlock, label: str) -> list[str]:
    errors: list[str] = []
    if BARE_DIRECT_REREAD_RE.search(mrp.body):
        errors.append(f"{label}: R(H,Delta) line must not be a bare heading")
    match = DIRECT_REREAD_RE.search(mrp.body)
    if not match:
        return errors
    value = match.group("body")
    if not re.search(r"(?i)\bheld routes rechecked\b", value):
        errors.append(f"{label}: R(H,Delta) line must record held routes rechecked")
    if not re.search(r"(?i)\blive remainder\s*:", value):
        errors.append(f"{label}: R(H,Delta) line must record live remainder")
    if not re.search(r"(?i)\brelease/next\s*:", value):
        errors.append(f"{label}: R(H,Delta) line must record release/next consequence")
    return errors


def field_diagnostics_content_errors(mrp: MrpBlock, label: str) -> list[str]:
    diagnostics = field(mrp.body, "Field diagnostics")
    if not diagnostics:
        return []
    errors: list[str] = []
    if not FIELD_DIAGNOSTICS_DIVERGENCE_RE.search(diagnostics):
        errors.append(f"{label}: Field diagnostics must include target-explicit ∇·B state")
    if not FIELD_DIAGNOSTICS_CURL_RE.search(diagnostics):
        errors.append(f"{label}: Field diagnostics must include target-explicit ∇×κ state")
    return errors


def check_sidecar(path: Path, text: str, mrp: MrpBlock, errors: list[str]) -> None:
    sidecar_path = sidecar_path_for(path)
    if not sidecar_path.is_file():
        return
    sidecar = extract_field_witness(load_json(sidecar_path))
    errors.extend(f"{sidecar_path}: {error}" for error in field_witness_graph_errors(sidecar))
    witness = parse_closure_witness(text)
    if witness is not None and sidecar is not None:
        errors.extend(
            f"{path} <-> {sidecar_path}: {error}"
            for error in compare_visible_to_field_witness(witness, sidecar)
        )
    if sidecar is None:
        errors.append(f"{sidecar_path}: field_witness missing")
        return
    reread_pressure = sidecar.get("reread_pressure")
    if not isinstance(reread_pressure, dict):
        errors.append(f"{sidecar_path}: field_witness.reread_pressure missing")
        return
    if reread_pressure.get("finding") != mrp.finding:
        errors.append(f"{sidecar_path}: reread_pressure finding does not match visible MRP")
    if not reread_pressure.get("route_gradient"):
        errors.append(f"{sidecar_path}: reread_pressure route_gradient missing")
    elif mrp.route_gradient and str(reread_pressure.get("route_gradient")) != mrp.route_gradient:
        errors.append(f"{sidecar_path}: reread_pressure route_gradient does not match visible MRP")
    if mrp.route_result_type and reread_pressure.get("route_result_type") != mrp.route_result_type:
        errors.append(f"{sidecar_path}: reread_pressure route_result_type does not match visible MRP")
    if not mrp.route_result_type and not reread_pressure.get("route_result_type"):
        errors.append(f"{sidecar_path}: reread_pressure route_result_type missing")
    if reread_pressure.get("route") != mrp.route:
        errors.append(f"{sidecar_path}: reread_pressure route does not match visible MRP")
    if reread_pressure.get("preemption_basis") != mrp.preemption_basis:
        errors.append(f"{sidecar_path}: reread_pressure preemption_basis does not match visible MRP")
    if reread_pressure.get("divergence_state") != first_state(mrp.divergence):
        errors.append(f"{sidecar_path}: reread_pressure divergence_state does not match visible ∇·T")
    if reread_pressure.get("curl_state") != first_state(mrp.curl):
        errors.append(f"{sidecar_path}: reread_pressure curl_state does not match visible ∇×T")
    activations = reread_pressure.get("pressure_activations")
    if not isinstance(activations, dict) or not activations:
        errors.append(f"{sidecar_path}: reread_pressure pressure_activations missing")
    else:
        for key, value in activations.items():
            if not activation_names_owner_or_gap(str(value)):
                errors.append(
                    f"{sidecar_path}: reread_pressure pressure activation {key} must name an owner, pressure class, or coverage gap"
                )
    non_claims = reread_pressure.get("non_claims")
    if not isinstance(non_claims, list) or not any(
        re.search(r"(?i)\b(?:uptake|acceptance|conversion|guidance|soul)\b", str(item))
        for item in non_claims
    ):
        errors.append(f"{sidecar_path}: reread_pressure non_claims must preserve uptake/guidance boundary")
    graph_delta = reread_pressure.get("graph_delta")
    if isinstance(graph_delta, dict):
        edges = graph_delta.get("edges_added")
        if mrp.finding == "genuine-dependent" and not edges:
            errors.append(f"{sidecar_path}: genuine-dependent MRP requires graph_delta.edges_added")


LIVE_PRESSURE_RE = re.compile(
    r"(?i)\b(?:remaining live|remains live|still live|live pressure|next live burden|"
    r"proportionality|hiddenness|coercive-guidance|source-worldview|moral-grounding|"
    r"owner-floor|owner-body|OWNER-BODY-NOT-LOADED)\b"
)
UNRELEASED_ROUTE_RE = re.compile(
    r"(?i)\b(?:identified but not released|not released as a new burden|unreleased|"
    r"held outside (?:this )?scope|remain outside|remains outside|held broad routes remain|"
    r"broad .* routes remain unreleased)\b"
)
NEGATED_UNRELEASED_RE = re.compile(
    r"(?i)\b(?:no|not|without|none)\s+"
    r"(?:remaining\s+|identified\s+|post-Land\s+|input-anchored\s+)*"
    r"(?:(?:burden(?:s)?|route(?:s)?|pressure)?\s*(?:remain(?:s)?\s+)?unreleased|live|remaining live)\b"
)
SCOPED_NON_ROUTE_OUTSIDE_RE = re.compile(
    r"(?i)\b(?:full public (?:polemical )?closure|downstream public refutation)\s+"
    r"remains\s+(?:out of scope|outside\b.{0,80}\bartifact\b)"
)
EXPLICIT_UNRELEASED_RE = re.compile(
    r"(?i)\b(?:identified but not released|not released as a new burden|unreleased|held broad routes remain|"
    r"broad .* routes remain unreleased)\b"
)


def has_unreleased_route(body: str) -> bool:
    if not UNRELEASED_ROUTE_RE.search(body):
        return False
    if re.search(r"(?i)\bno\b.{0,80}\b(?:remain(?:s|ing)?\s+)?unreleased\b", body):
        return False
    if SCOPED_NON_ROUTE_OUTSIDE_RE.search(body) and not EXPLICIT_UNRELEASED_RE.search(body):
        return False
    return not NEGATED_UNRELEASED_RE.search(body)


def has_high_leverage_unworked_route(body: str) -> bool:
    return bool(HIGH_LEVERAGE_ROUTE_RE.search(body) and HELD_OR_UNWORKED_ROUTE_RE.search(body))


def has_held_route_license(body: str) -> bool:
    return bool(HELD_ROUTE_LICENSE_RE.search(body))


def high_leverage_false_closure_errors(path: Path, mrp: MrpBlock, label: str) -> list[str]:
    """Reject STOP over named, still-held high-leverage routes without a license.

    This is intentionally selection-general: the regexes recognize route classes
    as examples of high leverage, but the failure is the generic route-state
    contradiction between a held/unworked route and terminal closure.
    """
    if mrp.route != "STOP":
        return []
    body = "\n".join(
        value
        for value in (
            mrp.body,
            mrp.reread,
            mrp.route_gradient,
            mrp.mrp_resultant,
            mrp.boundary,
        )
        if value
    )
    if not has_high_leverage_unworked_route(body):
        return []
    if has_held_route_license(body):
        return []
    return [
        f"{label}: STOP/closure cannot leave high-leverage held routes beyond prompt; "
        "execute the route, generate/activate the burden, HOLD/PARTIAL it, or prove it non-load-bearing"
    ]


def closure_over_held_route_errors(path: Path, text: str) -> list[str]:
    if not has_high_leverage_unworked_route(text):
        return []
    if not COMPLETE_CLOSURE_STATUS_RE.search(text):
        return []
    if has_held_route_license(text):
        return []
    return [
        f"{path}: output lists high-leverage routes as held beyond prompt but still claims complete closure"
    ]


def partial_owner_closure_errors(path: Path, text: str) -> list[str]:
    if not re.search(r"(?i)\bPARTIAL\s*/\s*OWNER-BODY-NOT-LOADED\b", text):
        return []
    errors: list[str] = []
    partial_at = re.search(r"(?i)\bPARTIAL\s*/\s*OWNER-BODY-NOT-LOADED\b", text)
    assert partial_at is not None
    tail = text[partial_at.start() :]
    if re.search(r"(?im)^\s*(?:#{1,6}\s*)?(?:Closure/Reconstruction Witness|Restorative Response|Closing Formulation)\b", tail):
        errors.append(f"{path}: OWNER-BODY-NOT-LOADED must not continue into closure/restorative/final sections")
    if re.search(r"(?i)\b(?:refuted at its root|refuted\b|closed\b|closure licensed|no unresolved burden)\b", tail):
        errors.append(f"{path}: OWNER-BODY-NOT-LOADED must not claim refutation/closure for the blocked burden")
    if re.search(r"(?im)^\s*Route\s*:\s*PARTIAL\b", text):
        errors.append(f"{path}: MRP owner-load failure must use Route: HOLD plus PARTIAL boundary, not Route: PARTIAL")
    return errors


def stop_before_continuation_errors(path: Path, text: str) -> list[str]:
    """Reject final STOP before later burden-local work in the same output."""
    errors: list[str] = []
    for match in STOP_ROUTE_RE.finditer(text):
        tail = text[match.end() :]
        continuation = POST_STOP_CONTINUATION_RE.search(tail)
        terminal = POST_STOP_TERMINAL_RE.search(tail)
        if continuation and (terminal is None or continuation.start() < terminal.start()):
            errors.append(f"{path}: Route: STOP cannot be followed by later burden/Layer B work before closure")
    return errors


def curl_diagnostic_errors(path: Path, mrp: MrpBlock, label: str) -> list[str]:
    """Reject use of curl for ordinary acyclic downstream dependencies."""
    errors: list[str] = []
    curl_state = first_state(mrp.curl)
    if curl_state in {"held", "non-null"}:
        if CURL_NEGATION_RE.search(mrp.curl):
            errors.append(f"{label}: {curl_state} ∇×T contradicts a no-loop/no-circularity reason")
        if LINEAR_DEPENDENCY_RE.search(mrp.curl) and not STRICT_CURL_REASON_RE.search(mrp.curl):
            errors.append(f"{label}: linear downstream dependency belongs to ∇·T; ∇×T must stay null without loop/churn/recoil")
    if curl_state == "resolved" and LINEAR_DEPENDENCY_RE.search(mrp.curl) and not CURL_REASON_RE.search(mrp.curl):
        errors.append(f"{label}: resolved ∇×T needs a prior real curl/loop reason, not ordinary dependency traversal")
    return errors


def route_result_type_errors(path: Path, mrp: MrpBlock, label: str) -> list[str]:
    """Validate optional MRP route-result type when visible."""
    errors: list[str] = []
    value = mrp.route_result_type.strip()
    if not value:
        return errors
    if value not in ROUTE_RESULT_TYPES:
        return [f"{label}: MRP route result type invalid: {value!r}"]
    if value == "generated_burden_instantiation":
        if mrp.route not in {"RECURSE", "HOLD"}:
            errors.append(f"{label}: generated_burden_instantiation requires Route: RECURSE or HOLD")
        if not has_edge(mrp.graph_delta):
            errors.append(f"{label}: generated_burden_instantiation requires visible graph edge")
        if mrp.preemption_basis == "none":
            errors.append(f"{label}: generated_burden_instantiation requires graph/commitment/framework-bound basis")
        if not mrp.route_gradient:
            errors.append(f"{label}: generated_burden_instantiation requires Route-gradient")
        elif not re.search(r"(?i)\b(?:generated|new|newly|resultant|not fully present|not present|MRP)\b", mrp.route_gradient):
            errors.append(f"{label}: generated_burden_instantiation Route-gradient must explain the newly surfaced resultant")
        elif not re.search(r"(?i)(?:Δ|Delta|xi|ξ|Omega|Ω|concealment|framework|dependency|burden-gradient|translation tribunal|admissibility|doctrine|mystery|immunity|shield|recoil|source-worldview|del[- ]dot|D3|D6)", mrp.route_gradient):
            errors.append(f"{label}: generated_burden_instantiation Route-gradient must name the post-Land pressure source")
    elif value == "held_burden_activation":
        if mrp.route not in {"RECURSE", "HOLD"}:
            errors.append(f"{label}: held_burden_activation requires Route: RECURSE or HOLD")
        if not has_edge(mrp.graph_delta):
            errors.append(f"{label}: held_burden_activation requires graph provenance edge")
        if not mrp.route_gradient:
            errors.append(f"{label}: held_burden_activation requires Route-gradient")
        elif not (
            re.search(r"(?i)\b(?:held|initial|already[- ]inventoried|already named|H\b)", mrp.route_gradient)
            or BURDEN_ARROW_TARGET_RE.search(mrp.route_gradient)
            or bool(edge_targets(mrp.graph_delta) & set(re.findall(r"(?:B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)", mrp.route_gradient)))
        ):
            errors.append(f"{label}: held_burden_activation Route-gradient must point to an already-held/initial burden")
    elif value == "no_new_resultant":
        if has_edge(mrp.graph_delta):
            errors.append(f"{label}: no_new_resultant must not create a graph edge")
    elif value == "loopbreak":
        if mrp.route != "LoopBreak(∇×T)":
            errors.append(f"{label}: loopbreak route result type requires Route: LoopBreak(∇×T)")
        if has_edge(mrp.graph_delta):
            errors.append(f"{label}: loopbreak must not create graph edge")
    elif value == "hold_partial" and mrp.route != "HOLD":
        errors.append(f"{label}: hold_partial route result type requires Route: HOLD")
    return errors


def check_mrp_block(path: Path, text: str, mrp: MrpBlock, index: int) -> list[str]:
    label = f"{path}: MRP block {index}"
    errors: list[str] = []
    if not mrp.target or "B" not in mrp.target:
        errors.append(f"{label}: Target must name a burden")
    if not mrp.reread or not re.search(r"R\(H,\s*(?:Δ|Delta)\)", mrp.reread):
        errors.append(f"{label}: Reread must invoke R(H,Δ)")
    errors.extend(direct_reread_content_errors(mrp, label))
    if not mrp.landed_delta or not re.search(r"(?:ΔⁿB|Δ|Delta)", mrp.landed_delta):
        errors.append(f"{label}: Landed delta must name ΔⁿB/Δ")
    if not mrp.route_gradient:
        errors.append(f"{label}: Route-gradient must record the plain-∇ directional read")
    divergence_state = first_state(mrp.divergence)
    curl_state = first_state(mrp.curl)
    if not mrp.divergence or divergence_state not in ALLOWED_DIVERGENCE:
        errors.append(f"{label}: must record active ∇·T state")
    if not mrp.curl or curl_state not in ALLOWED_CURL:
        errors.append(f"{label}: must record active ∇×T state")
    errors.extend(field_diagnostics_content_errors(mrp, label))
    missing_pressure = sorted(PRESSURE_KEYS - set(mrp.pressure_lines))
    for key in missing_pressure:
        errors.append(f"{label}: Pressure activations missing {key}")
    for key, value in mrp.pressure_lines.items():
        if not activation_names_owner_or_gap(value):
            errors.append(f"{label}: pressure activation {key} must name an owner/TTP, pressure class, or coverage gap")
    if mrp.finding not in FINDINGS:
        errors.append(f"{label}: Finding invalid: {mrp.finding!r}")
    if not mrp.route_result_type:
        errors.append(f"{label}: MRP route result type missing")
    errors.extend(route_result_type_errors(path, mrp, label))
    errors.extend(mrp_refutation_content_errors(mrp, label))
    if not mrp.graph_delta:
        errors.append(f"{label}: Graph delta missing")
    if mrp.route not in ROUTES:
        errors.append(f"{label}: Route invalid: {mrp.route!r}")
    if mrp.finding == "stable" and (mrp.route != "STOP" or not is_none_delta(mrp.graph_delta)):
        errors.append(f"{label}: stable finding requires STOP and no graph edge")
    if mrp.finding == "genuine-dependent" and (mrp.route != "RECURSE" or not has_edge(mrp.graph_delta)):
        errors.append(f"{label}: genuine-dependent finding requires RECURSE and graph edge")
    if mrp.finding == "partial-real" and mrp.route != "HOLD":
        errors.append(f"{label}: partial-real finding requires HOLD")
    if has_edge(mrp.graph_delta) and mrp.preemption_basis == "none":
        errors.append(f"{label}: graph-edge pre-emption requires graph/commitment/framework-bound basis")
    if mrp.route == "STOP" and LIVE_PRESSURE_RE.search(mrp.body):
        if not re.search(r"(?i)\b(?:held|HOLD|PARTIAL|landed|merged|cleared|bounded)\b", mrp.body):
            errors.append(f"{label}: STOP cannot leave named live pressure unreleased, unheld, or unpartialed")
    if mrp.route == "STOP" and has_unreleased_route(mrp.body):
        errors.append(f"{label}: STOP cannot leave an identified post-Land escape route unreleased; generate, HOLD/PARTIAL, or LoopBreak it")
    errors.extend(high_leverage_false_closure_errors(path, mrp, label))
    return errors


def check_mrp_block(path: Path, text: str, mrp: MrpBlock, index: int) -> list[str]:
    """Validate any MRP block after the first one.

    This intentionally shadows the legacy helper above, whose regexes were tied to a stale
    mojibake spelling of Delta. Multi-burden hosted smokes need every block to be checked with
    the same route/resultant contract as the first block.
    """
    label = f"{path}: MRP block {index}"
    errors: list[str] = []
    if not mrp.target or "B" not in mrp.target:
        errors.append(f"{label}: Target must name a burden")
    if not mrp.reread or not REREAD_RE.search(mrp.reread):
        errors.append(f"{label}: Reread must invoke R(H,Delta)")
    errors.extend(direct_reread_content_errors(mrp, label))
    if not mrp.landed_delta or not LANDED_DELTA_RE.search(mrp.landed_delta):
        errors.append(f"{label}: Landed delta must name Delta/Δ")
    if not mrp.route_gradient:
        errors.append(f"{label}: Route-gradient must record the plain-∇ directional read")
    divergence_state = first_state(mrp.divergence)
    curl_state = first_state(mrp.curl)
    if not mrp.divergence or divergence_state not in ALLOWED_DIVERGENCE:
        errors.append(f"{label}: must record active divergence state")
    if not mrp.curl or curl_state not in ALLOWED_CURL:
        errors.append(f"{label}: must record active curl state")
    errors.extend(field_diagnostics_content_errors(mrp, label))
    errors.extend(curl_diagnostic_errors(path, mrp, label))
    missing_pressure = sorted(PRESSURE_KEYS - set(mrp.pressure_lines))
    for key in missing_pressure:
        errors.append(f"{label}: Pressure activations missing {key}")
    for key, value in mrp.pressure_lines.items():
        if not activation_names_owner_or_gap(value):
            errors.append(f"{label}: pressure activation {key} must name an owner/TTP, pressure class, or coverage gap")
    if mrp.finding not in FINDINGS:
        errors.append(f"{label}: Finding invalid: {mrp.finding!r}")
    if not mrp.route_result_type:
        errors.append(f"{label}: MRP route result type missing")
    errors.extend(route_result_type_errors(path, mrp, label))
    errors.extend(mrp_refutation_content_errors(mrp, label))
    if not mrp.mrp_resultant:
        errors.append(f"{label}: MRP resultant missing")
    if not mrp.graph_delta:
        errors.append(f"{label}: Graph delta missing")
    if mrp.route not in ROUTES:
        errors.append(f"{label}: Route invalid: {mrp.route!r}")
    if mrp.preemption_basis not in {"none", "graph-bound", "commitment-bound", "framework-bound"}:
        errors.append(f"{label}: Pre-emption basis invalid: {mrp.preemption_basis!r}")
    if not re.search(r"T_lang", mrp.boundary) or re.search(
        r"(?i)\b(?:guarantees|ensures|proves|achieves)\b.{0,50}\b(?:uptake|acceptance|conversion|guidance)\b",
        mrp.boundary,
    ):
        errors.append(f"{label}: Boundary must preserve T_lang non-guaranteed uptake")
    if mrp.finding == "stable" and (mrp.route != "STOP" or not is_none_delta(mrp.graph_delta)):
        errors.append(f"{label}: stable finding requires STOP and no graph edge")
    if mrp.finding == "genuine-dependent" and (mrp.route != "RECURSE" or not has_edge(mrp.graph_delta)):
        errors.append(f"{label}: genuine-dependent finding requires RECURSE and graph edge")
    if mrp.finding == "partial-real" and mrp.route != "HOLD":
        errors.append(f"{label}: partial-real finding requires HOLD")
    if has_edge(mrp.graph_delta) and mrp.preemption_basis == "none":
        errors.append(f"{label}: graph-edge pre-emption requires graph/commitment/framework-bound basis")
    if mrp.route == "STOP" and LIVE_PRESSURE_RE.search(mrp.body):
        if not re.search(r"(?i)\b(?:held|HOLD|PARTIAL|landed|merged|cleared|bounded)\b", mrp.body):
            errors.append(f"{label}: STOP cannot leave named live pressure unreleased, unheld, or unpartialed")
    if mrp.route == "STOP" and has_unreleased_route(mrp.body):
        errors.append(f"{label}: STOP cannot leave an identified post-Land escape route unreleased; generate, HOLD/PARTIAL, or LoopBreak it")
    errors.extend(high_leverage_false_closure_errors(path, mrp, label))
    return errors


def per_land_mrp_coverage_errors(path: Path, text: str) -> list[str]:
    """Require one visible MRP block per line-start landing gate.

    Canonical per-burden MRP visibility: every public `Land(ⁿB):` landing gate
    must be followed by a `[Mid-Reread Pressure]` heading before the next
    landing gate (or end of output for the final burden). A single terminal
    block covering multiple landings is the staged-shape projection-thinning
    failure class: per-burden reread state then lives only in
    `field_witness.formal_reread_states[]` while the public surface
    under-mirrors it.
    """
    gates = list(LAND_GATE_RE.finditer(text))
    if not gates:
        return []
    headings = [match.start() for match in re.finditer(MRP_HEADING_RE, text, re.MULTILINE)]
    errors: list[str] = []
    for index, gate in enumerate(gates):
        window_end = gates[index + 1].start() if index + 1 < len(gates) else len(text)
        if not any(gate.end() <= position < window_end for position in headings):
            errors.append(
                f"{path}: Land({gate.group('burden')}) landing gate has no "
                "[Mid-Reread Pressure] block before the next landing gate; "
                "per-burden MRP visibility is required and a single terminal "
                "block must not cover multiple landings"
            )
    return errors


def check_fixture(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    errors.extend(partial_owner_closure_errors(path, text))
    errors.extend(stop_before_continuation_errors(path, text))
    errors.extend(closure_over_held_route_errors(path, text))
    mrp = parse_mrp(text)
    if mrp is None:
        return [f"{path}: missing [Mid-Reread Pressure] block"]
    if not mrp.mrp_resultant:
        errors.append(f"{path}: MRP resultant missing")
    all_mrps = parse_mrps(text)
    for index, block in enumerate(all_mrps[1:], start=2):
        errors.extend(check_mrp_block(path, text, block, index))
    errors.extend(per_land_mrp_coverage_errors(path, text))

    if not mrp.target or "B" not in mrp.target:
        errors.append(f"{path}: MRP Target must name a burden")
    if not mrp.reread or not re.search(r"R\(H,\s*(?:Δ|Delta)\)", mrp.reread):
        errors.append(f"{path}: MRP Reread must invoke R(H,Δ)")
    errors.extend(direct_reread_content_errors(mrp, str(path)))
    if not mrp.landed_delta or not re.search(r"(?:ΔⁿB|Δ|Delta)", mrp.landed_delta):
        errors.append(f"{path}: MRP Landed delta must name ΔⁿB/Δ")
    if not mrp.route_gradient:
        errors.append(f"{path}: MRP Route-gradient must record the plain-∇ directional read")
    divergence_state = first_state(mrp.divergence)
    curl_state = first_state(mrp.curl)
    if not mrp.divergence or divergence_state not in ALLOWED_DIVERGENCE:
        errors.append(f"{path}: MRP must record active ∇·T state: neutral/settled/bounded/non-neutral")
    if not mrp.curl or curl_state not in ALLOWED_CURL:
        errors.append(f"{path}: MRP must record active ∇×T state: null/resolved/held/non-null")
    errors.extend(field_diagnostics_content_errors(mrp, str(path)))
    errors.extend(curl_diagnostic_errors(path, mrp, str(path)))
    missing_pressure = sorted(PRESSURE_KEYS - set(mrp.pressure_lines))
    for key in missing_pressure:
        errors.append(f"{path}: MRP Pressure activations missing {key}")
    for key, value in mrp.pressure_lines.items():
        if not activation_names_owner_or_gap(value):
            errors.append(
                f"{path}: MRP pressure activation {key} must name an existing owner/TTP, pressure class, or coverage gap"
            )
    if mrp.finding not in FINDINGS:
        errors.append(f"{path}: MRP Finding invalid: {mrp.finding!r}")
    if not mrp.route_result_type:
        errors.append(f"{path}: MRP route result type missing")
    errors.extend(route_result_type_errors(path, mrp, str(path)))
    errors.extend(mrp_refutation_content_errors(mrp, str(path)))
    if not mrp.graph_delta:
        errors.append(f"{path}: MRP Graph delta missing")
    if mrp.route not in ROUTES:
        errors.append(f"{path}: MRP Route invalid: {mrp.route!r}")
    if mrp.preemption_basis not in {"none", "graph-bound", "commitment-bound", "framework-bound"}:
        errors.append(f"{path}: MRP Pre-emption basis invalid: {mrp.preemption_basis!r}")
    if not re.search(r"T_lang", mrp.boundary) or re.search(
        r"(?i)\b(?:guarantees|ensures|proves|achieves)\b.{0,50}\b(?:uptake|acceptance|conversion|guidance)\b",
        mrp.boundary,
    ):
        errors.append(f"{path}: MRP Boundary must preserve T_lang non-guaranteed uptake")
    if re.search(r"(?i)T_lang.{0,80}(?:guarantees|ensures|proves|achieves).{0,80}(?:uptake|acceptance|conversion|guidance)", text):
        errors.append(f"{path}: T_lang guaranteed uptake claim")

    if mrp.reread and not (mrp.finding and mrp.route and mrp.graph_delta):
        errors.append(f"{path}: R(H,Δ) invoked without observable MRP consequence")

    if mrp.route == "RECURSE" and not has_edge(mrp.graph_delta):
        errors.append(f"{path}: RECURSE requires visible graph delta edge")
    if mrp.route == "STOP" and has_unreleased_route(mrp.body):
        errors.append(f"{path}: STOP cannot leave an identified post-Land escape route unreleased; generate, HOLD/PARTIAL, or LoopBreak it")
    errors.extend(high_leverage_false_closure_errors(path, mrp, str(path)))
    if mrp.finding == "genuine-dependent" and (mrp.route != "RECURSE" or not has_edge(mrp.graph_delta)):
        errors.append(f"{path}: genuine-dependent finding requires RECURSE and graph edge")
    if has_edge(mrp.graph_delta) and mrp.preemption_basis == "none":
        errors.append(f"{path}: graph-edge pre-emption requires graph-bound, commitment-bound, or framework-bound basis")
    preemption_text = re.sub(r"(?im)^\s*Pre-emption basis\s*:.*$", "", text)
    if re.search(
        r"(?i)\b(?:likely defense|pre-voiced recoil|anticipatory downstream pressure|"
        r"pre-emption|pre-empted burden|structurally licensed defense)\b",
        preemption_text,
    ):
        if mrp.preemption_basis == "none":
            errors.append(f"{path}: anticipatory downstream pressure requires a non-speculative pre-emption basis")
        if not re.search(r"(?i)\b(?:graph-bound|commitment-bound|framework-bound|structurally licensed)\b", preemption_text):
            errors.append(f"{path}: anticipatory downstream pressure must be graph/commitment/framework bound")
        if not any(
            re.search(r"\b(?:foreign-premise-detection|M1-self-refutation|M1P-performative-self-refutation|M8-reductio|M7-definition-anchor|doubt-vs-skepticism|V3-regress-dissolution|R2-the-reminder|P1-fitrah-restoration)\b", value)
            for value in mrp.pressure_lines.values()
        ):
            errors.append(f"{path}: anticipatory downstream pressure must name the existing TTP/operator used")
    if mrp.finding == "stable" and (mrp.route != "STOP" or not is_none_delta(mrp.graph_delta)):
        errors.append(f"{path}: stable finding requires STOP and no graph edge")
    if mrp.finding == "stable" and (
        divergence_state not in {"neutral", "settled", "bounded"} or curl_state not in {"null", "resolved"}
    ):
        errors.append(f"{path}: stable closure requires neutral/settled ∇·T and null/resolved ∇×T")
    if mrp.finding == "partial-real" and mrp.route != "HOLD":
        errors.append(f"{path}: partial-real finding requires HOLD")
    if divergence_state == "non-neutral" and mrp.route not in {"HOLD", "RECURSE"}:
        errors.append(f"{path}: non-neutral ∇·T requires HOLD or RECURSE explanation")
    if curl_state == "non-null" and mrp.route not in {"STOP", "HOLD", "RECURSE", "LoopBreak(∇×T)"}:
        errors.append(f"{path}: non-null ∇×T requires STOP/HOLD/RECURSE/LoopBreak route")
    if curl_state == "non-null" and mrp.route == "RECURSE" and not has_edge(mrp.graph_delta):
        errors.append(f"{path}: non-null ∇×T recursion requires graph-bound edge if it is not LoopBreak/STOP/HOLD")
    if curl_state in {"held", "non-null"}:
        has_non_load_bearing_proof = bool(
            re.search(
                r"(?i)\b(?:non[- ]load[- ]bearing|not load[- ]bearing|outside scope|not operative|"
                r"framework[- ]concession[- ]bound|not an ordinary downstream burden|no ordinary downstream burden|"
                r"no ordinary graph edge)\b",
                mrp.body,
            )
        )
        if mrp.route == "STOP" and mrp.route_result_type != "loopbreak" and not has_non_load_bearing_proof:
            errors.append(
                f"{path}: nonzero ∇×T cannot STOP without LoopBreak, HOLD/PARTIAL/RECURSE, or non-load-bearing proof"
            )
    if mrp.route == "LoopBreak(∇×T)" and curl_state not in {"held", "non-null"}:
        errors.append(f"{path}: LoopBreak(∇×T) requires diagnosed nonzero ∇×T")
    if mrp.finding == "hidden-framework-recoil":
        if not re.search(r"framework-concession-bound|hidden-framework", text, re.IGNORECASE):
            errors.append(f"{path}: hidden-framework-recoil must mark framework-concession boundary")
        if re.search(r"(?i)unqualified landed burden", text):
            errors.append(f"{path}: hidden-framework recoil treated as unqualified landed burden")
    if mrp.finding == "doubt-churn":
        if mrp.route not in {"STOP", "LoopBreak(∇×T)"}:
            errors.append(f"{path}: doubt-churn requires STOP or LoopBreak(∇×T)")
        if has_edge(mrp.graph_delta):
            errors.append(f"{path}: doubt-churn must not create ordinary graph edge")
        if has_positive_proof_stacking_after_doubt_churn(text):
            errors.append(f"{path}: proof-stacking after doubt-churn")
    if mrp.finding == "reorientation":
        if not re.search(r"(?i)(?:already-landed signs|prior stable knowledge|fiṭrah|ʿaql ṣarīḥ)", text):
            errors.append(f"{path}: reorientation must name prior stable knowledge/signs")
        if has_edge(mrp.graph_delta):
            errors.append(f"{path}: reorientation must not create unnecessary graph edge")

    witness = parse_closure_witness(text)
    if witness is not None:
        errors.extend(f"{path}: {error}" for error in closure_witness_errors(witness))
        if mrp.finding == "partial-real" and not any(
            payload.get("state") in {"held-with-reason", "carried-PARTIAL"} for payload in witness.terminal_states.values()
        ):
            errors.append(f"{path}: partial-real finding requires held/PARTIAL terminal accounting")
        if mrp.finding == "genuine-dependent" and not witness.edges:
            errors.append(f"{path}: genuine-dependent finding requires closure graph edge")
    check_sidecar(path, text, mrp, errors)
    return errors


def check_output_reconstructibility(path: Path) -> list[str]:
    """Hosted-smoke guard: MRP must be part of reconstructible node accounting."""
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    partial_owner = bool(re.search(r"(?i)\bPARTIAL\s*/\s*OWNER-BODY-NOT-LOADED\b", text))
    hold_route = bool(re.search(r"(?im)^\s*Route\s*:\s*HOLD\b", text))

    if not re.search(r"(?im)^\s*(?:Burden\s+\d+|Initial burden set\s*:)", text):
        errors.append(f"{path}: reconstructibility missing burden nodes")
    if not partial_owner and not re.search(
        r"(?im)^\s*(?:Operative Submove|[¹1]B[₁₂₃₄₅₆₇₈₉0-9]|Target\s*:)",
        text,
    ):
        errors.append(f"{path}: reconstructibility missing submove nodes")
    if not re.search(r"(?im)^\s*(?:Land\(|Landed delta\s*:|Land\(Bn\)\s*:\s*PARTIAL)", text):
        errors.append(f"{path}: reconstructibility missing Land(Bn) or partial landing")
    if not re.search(r"(?im)^\s*(?:[-*]\s*)?(?:Reread\s*:\s*)?R\(H,\s*(?:Delta|Δ)\)(?::|\b)", text):
        errors.append(f"{path}: reconstructibility missing R(H,Delta) reread state")
    if not re.search(r"(?im)^\s*MRP resultant\s*:\s*\S", text):
        errors.append(f"{path}: reconstructibility missing MRP resultant")
    if not re.search(r"(?im)^\s*(?:Graph delta\s*:|Burden dependency graph\s*:|field_witness\b)", text):
        errors.append(f"{path}: reconstructibility missing graph/field_witness consequence")
    if not re.search(r"(?im)^\s*Route\s*:\s*(?:STOP|HOLD|RECURSE|LoopBreak)", text):
        errors.append(f"{path}: reconstructibility missing route consequence")
    if not re.search(r"(?i)T_lang", text):
        errors.append(f"{path}: reconstructibility missing T_lang non-guaranteed-uptake boundary")
    if not partial_owner and not re.search(r"(?im)^\s*Initial burden set\s*:\s*\[", text):
        errors.append(f"{path}: reconstructibility missing initial burden set")
    if not partial_owner and not re.search(r"(?im)^\s*Terminal states\s*:", text):
        errors.append(f"{path}: reconstructibility missing terminal-state accounting")
    if not partial_owner and not re.search(r"(?im)^\s*(?:#{1,6}\s*)?(?:(?:Final\s+)?Restorative Response\b|PARTIAL\s*-\s*bounded\s+answer\b)|restoration aim", text):
        errors.append(f"{path}: reconstructibility missing closure/restoration relation")
    if partial_owner or hold_route:
        if not re.search(r"(?i)\b(?:next live burden|held-with-reason|carried-PARTIAL|Route\s*:\s*HOLD|PARTIAL)\b", text):
            errors.append(f"{path}: HOLD/PARTIAL route missing held burden accounting")
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    valid = sorted((root / "valid").glob("*.md"))
    invalid = sorted((root / "invalid").glob("*.md"))
    return valid, invalid


def expand_output_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(marker in raw for marker in "*?[]"):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/mid-reread-pressure"))
    parser.add_argument(
        "--outputs",
        nargs="*",
        type=Path,
        default=[],
        help="Optional live/hosted smoke output files to validate against the MRP block contract.",
    )
    args = parser.parse_args()

    root = args.root
    valid, invalid = iter_fixtures(root)
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    valid_blocks: list[tuple[Path, MrpBlock]] = []
    for path in valid:
        found = check_fixture(path)
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
            parsed = parse_mrp(path.read_text(encoding="utf-8", errors="replace"))
            if parsed is not None:
                valid_blocks.append((path, parsed))
    for path in invalid:
        found = check_fixture(path)
        if not found:
            errors.append(f"{path}: expected-invalid fixture unexpectedly passed")
        else:
            invalid_checked += 1
    output_checked = 0
    output_paths = expand_output_paths(args.outputs)
    for path in output_paths:
        found = check_fixture(path)
        found.extend(check_output_reconstructibility(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1
    has_contraction = any(
        block.finding in {"doubt-churn", "hidden-framework-recoil"}
        and block.route in {"STOP", "LoopBreak(∇×T)"}
        and not has_edge(block.graph_delta)
        for _, block in valid_blocks
    )
    has_expansion = any(
        block.finding == "genuine-dependent"
        and block.route == "RECURSE"
        and has_edge(block.graph_delta)
        for _, block in valid_blocks
    )
    has_preemption = any(
        block.preemption_basis in {"graph-bound", "commitment-bound", "framework-bound"}
        and has_edge(block.graph_delta)
        and re.search(
            r"(?i)\b(?:likely defense|pre-voiced recoil|anticipatory downstream pressure|pre-empt|structurally licensed)\b",
            path.read_text(encoding="utf-8", errors="replace"),
        )
        for path, block in valid_blocks
    )
    has_hold = any(block.finding == "partial-real" and block.route == "HOLD" for _, block in valid_blocks)
    if not has_contraction:
        errors.append("valid fixture suite missing contraction case: churn/unlicensed recoil -> STOP or LoopBreak without graph edge")
    if not has_expansion:
        errors.append("valid fixture suite missing expansion case: genuine downstream burden -> RECURSE with graph edge")
    if not has_preemption:
        errors.append("valid fixture suite missing pre-emption case: structurally licensed recoil -> graph-bound dispatch")
    if not has_hold:
        errors.append("valid fixture suite missing hold case: partial real burden -> HOLD")
    if errors:
        print("mid-reread pressure check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("mid-reread pressure check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if output_paths:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
