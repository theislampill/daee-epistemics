#!/usr/bin/env python3
"""Render Closure/Reconstruction Witness text or field_witness JSON.

The output is a research/evaluation artifact. It visualizes rendered coverage
structure; it does not prove live noetic competence.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    closure_witness_errors,
    compare_visible_to_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    graph_nodes,
    load_json,
    parse_closure_witness,
)


CLASS_BY_STATE = {
    "landed": "landed",
    "discharged-as-derivative": "discharged",
    "held-with-reason": "held",
    "carried-PARTIAL": "carried",
    "carried-RECURSE": "carried",
    "cleared": "cleared",
    "missing terminal state": "missing",
}


COLOR_BY_CLASS = {
    "landed": "#7cc8ff",
    "discharged": "#b9dcff",
    "held": "#fff2a8",
    "carried": "#ffd1a8",
    "cleared": "#b7f7c1",
    "missing": "#ffc4c4",
}


def mermaid_escape(value: str) -> str:
    return value.replace('"', "'").replace("\n", "<br/>")


def node_label(burden: str, state: str, detail: str) -> str:
    if detail:
        return f'{burden}["{burden}<br/>{mermaid_escape(state)}<br/>{mermaid_escape(detail[:80])}"]'
    return f'{burden}["{burden}<br/>{mermaid_escape(state)}"]'


def summary_from_visible(witness, errors: list[str]) -> dict[str, Any]:  # noqa: ANN001
    burdens = list(dict.fromkeys(witness.initial_burdens + list(witness.terminal_states) + witness.graph_nodes))
    nodes = []
    for burden in burdens:
        payload = witness.terminal_states.get(burden)
        if payload:
            detail = payload["detail"]
            operator = detail.split("/", 1)[0].strip() if "/" in detail else ""
            nodes.append(
                {
                    "id": burden,
                    "state": payload["state"],
                    "operator": operator,
                    "detail": detail,
                    "coverage": "present",
                }
            )
        else:
            nodes.append(
                {
                    "id": burden,
                    "state": "missing terminal state",
                    "operator": "",
                    "detail": "",
                    "coverage": "missing",
                }
            )
    return {
        "source_type": "visible_closure_witness",
        "initial_burden_set": witness.initial_burdens,
        "registers": witness.registers,
        "terminal_states": witness.terminal_states,
        "nodes": nodes,
        "edges": [{"from": src, "to": target, "kind": "depends-on"} for src, target in witness.edges],
        "roots": witness.roots,
        "parallel_groups": witness.parallel_groups,
        "divergence": witness.divergence,
        "curl": witness.curl,
        "closure": witness.closure,
        "transfer": witness.transfer,
        "coverage_complete": witness.coverage_complete,
        "collapse_positive": witness.collapse_positive,
        "errors": errors,
    }


def summary_from_field_witness(field_witness: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    coverage = field_witness.get("coverage_proof", {})
    graph = coverage.get("dependency_graph", {})
    terminals = coverage.get("terminal_states", {})
    nodes = []
    for burden in graph.get("nodes", []):
        payload = terminals.get(burden, {}) if isinstance(terminals, dict) else {}
        detail = payload.get("delta_nB") or payload.get("reason") or ""
        nodes.append(
            {
                "id": burden,
                "state": payload.get("state", "missing terminal state"),
                "operator": payload.get("operator", ""),
                "detail": detail,
                "coverage": "present" if burden in terminals else "missing",
            }
        )
    diagnostics = field_witness.get("field_diagnostics", {})
    return {
        "source_type": "field_witness",
        "initial_burden_set": coverage.get("initial_burden_set", []),
        "terminal_states": terminals,
        "nodes": nodes,
        "edges": [{"from": edge.get("from"), "to": edge.get("to"), "kind": "depends-on"} for edge in graph.get("edges", [])],
        "roots": graph.get("roots", []),
        "parallel_groups": graph.get("parallel_groups", []),
        "divergence": coverage.get("divergence_check") or diagnostics.get("divergence", {}).get("status", ""),
        "curl": coverage.get("curl_check") or diagnostics.get("curl", {}).get("status", ""),
        "closure": field_witness.get("closure", {}).get("decision", ""),
        "transfer": field_witness.get("transfer_boundary", {}).get("mode", ""),
        "coverage_complete": coverage.get("coverage_complete", False),
        "collapse_positive": (
            coverage.get("coverage_complete") is True
            and str(coverage.get("divergence_check", "")).split("/", 1)[0].strip().lower() == "neutral"
            and str(coverage.get("curl_check", "")).split("/", 1)[0].strip().lower() in {"null", "resolved"}
        ),
        "register_deltas": field_witness.get("register_deltas", {}),
        "non_claims": field_witness.get("non_claims", []),
        "provenance": field_witness.get("provenance", {}),
        "errors": errors,
    }


def render_mermaid(payload: dict[str, Any]) -> str:
    lines = [
        "```mermaid",
        "flowchart TD",
        "  classDef landed fill:#7cc8ff,stroke:#1f5f8b,color:#111;",
        "  classDef discharged fill:#b9dcff,stroke:#2c5f91,color:#111;",
        "  classDef held fill:#fff2a8,stroke:#8a6d00,color:#111;",
        "  classDef carried fill:#ffd1a8,stroke:#9a4f00,color:#111;",
        "  classDef cleared fill:#b7f7c1,stroke:#227a3a,color:#111;",
        "  classDef missing fill:#ffc4c4,stroke:#a00000,color:#111;",
    ]
    for node in payload["nodes"]:
        lines.append("  " + node_label(str(node["id"]), str(node["state"]), str(node.get("detail") or "")))
    for edge in payload["edges"]:
        lines.append(f"  {edge['from']} --> {edge['to']}")
    for node in payload["nodes"]:
        class_name = CLASS_BY_STATE.get(str(node["state"]), "missing")
        lines.append(f"  class {node['id']} {class_name};")
    lines.append("```")
    return "\n".join(lines)


def render_markdown(path: Path, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Closure Witness Visualization",
            "",
            f"Source: `{path.as_posix()}`",
            "",
            f"- source_type: `{payload['source_type']}`",
            f"- coverage_complete: `{str(payload['coverage_complete']).lower()}`",
            f"- collapse_positive: `{str(payload['collapse_positive']).lower()}`",
            f"- ∇·B: `{payload.get('divergence') or 'missing'}`",
            f"- ∇×κ: `{payload.get('curl') or 'missing'}`",
            "",
            "## Mermaid DAG",
            "",
            render_mermaid(payload),
            "",
            "## Parsed JSON",
            "",
            "```json",
            json.dumps(payload, indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    )


def svg_layout(payload: dict[str, Any]) -> str:
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    index = {node["id"]: i for i, node in enumerate(nodes)}
    width = max(760, 180 * max(1, len(nodes)))
    height = 360
    positions: dict[str, tuple[int, int]] = {}
    for i, node in enumerate(nodes):
        positions[node["id"]] = (90 + (i * 160), 140 + ((i % 2) * 90))
    edge_lines = []
    for edge in edges:
        source = edge.get("from")
        target = edge.get("to")
        if source not in positions or target not in positions:
            continue
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        edge_lines.append(
            f'<line x1="{x1 + 48}" y1="{y1}" x2="{x2 - 48}" y2="{y2}" class="edge" marker-end="url(#arrow)" />'
        )
    node_lines = []
    for node in nodes:
        x, y = positions[node["id"]]
        class_name = CLASS_BY_STATE.get(str(node.get("state")), "missing")
        color = COLOR_BY_CLASS[class_name]
        label = html.escape(str(node["id"]))
        state = html.escape(str(node.get("state", "")))
        detail = html.escape(str(node.get("detail", ""))[:70])
        node_lines.append(
            f'<g class="node" data-node="{label}">'
            f'<rect x="{x - 54}" y="{y - 34}" width="108" height="68" rx="8" fill="{color}" />'
            f'<text x="{x}" y="{y - 10}" text-anchor="middle" class="node-id">{label}</text>'
            f'<text x="{x}" y="{y + 9}" text-anchor="middle">{state}</text>'
            f'<title>{label}: {state} {detail}</title>'
            f'</g>'
        )
    parallel = html.escape("; ".join(" ∥ ".join(group) for group in payload.get("parallel_groups", [])) or "none")
    return f"""
<svg viewBox="0 0 {width} {height}" role="img" aria-label="Closure witness burden DAG">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#333" />
    </marker>
  </defs>
  <text x="24" y="30" class="caption">Dependency edges: A → B means B depends on A landing first. Parallel groups: {parallel}</text>
  {''.join(edge_lines)}
  {''.join(node_lines)}
</svg>
"""


def render_html(path: Path, payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Closure Witness DAG</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; background: #f7f7f4; color: #151515; }}
main {{ max-width: 1180px; margin: auto; }}
textarea {{ width: 100%; min-height: 180px; font: 13px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; }}
.panel {{ background: white; border: 1px solid #d8d8d0; border-radius: 8px; padding: 16px; margin: 16px 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.metric {{ background: #f0f4f7; border-radius: 6px; padding: 10px; }}
.edge {{ stroke: #333; stroke-width: 2; }}
.node rect {{ stroke: #333; stroke-width: 1.5; }}
.node text {{ font-size: 12px; pointer-events: none; }}
.node-id {{ font-weight: 700; font-size: 16px; }}
.caption {{ font-size: 13px; fill: #333; }}
.error {{ color: #9a0000; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #111; color: #f6f6f6; padding: 12px; border-radius: 6px; }}
</style>
<main>
  <h1>Closure Witness DAG</h1>
  <p>Source: <code>{html.escape(path.as_posix())}</code>. This artifact renders visible closure-witness text or <code>field_witness</code> JSON. It is diagnostic evidence, not package-bound release proof.</p>
  <section class="panel">
    <h2>Graph</h2>
    {svg_layout(payload)}
  </section>
  <section class="grid">
    <div class="metric"><strong>source</strong><br>{html.escape(str(payload.get('source_type')))}</div>
    <div class="metric"><strong>coverage_complete</strong><br>{html.escape(str(payload.get('coverage_complete')))}</div>
    <div class="metric"><strong>collapse_positive</strong><br>{html.escape(str(payload.get('collapse_positive')))}</div>
    <div class="metric"><strong>∇·B / ∇×κ</strong><br>{html.escape(str(payload.get('divergence')))} / {html.escape(str(payload.get('curl')))}</div>
  </section>
  <section class="panel">
    <h2>Parse errors</h2>
    <pre class="error">{html.escape(chr(10).join(payload.get('errors') or ['none']))}</pre>
  </section>
  <section class="panel">
    <h2>Parsed payload</h2>
    <textarea id="payload"></textarea>
  </section>
</main>
<script>
const payload = {payload_json};
document.getElementById("payload").value = JSON.stringify(payload, null, 2);
</script>
</html>
"""


def payload_from_input(path: Path, field_witness_path: Path | None = None) -> tuple[dict[str, Any], int]:
    if path.suffix.lower() == ".json":
        field_witness = extract_field_witness(load_json(path))
        errors = field_witness_graph_errors(field_witness)
        if field_witness is None:
            return {"source_type": "field_witness", "nodes": [], "edges": [], "errors": errors}, 1
        return summary_from_field_witness(field_witness, errors), 0 if not errors else 1

    text = path.read_text(encoding="utf-8", errors="replace")
    witness = parse_closure_witness(text)
    if witness is None:
        return {"source_type": "visible_closure_witness", "nodes": [], "edges": [], "errors": ["missing Closure/Reconstruction Witness block"]}, 1
    errors = closure_witness_errors(witness)
    if field_witness_path:
        field_witness = extract_field_witness(load_json(field_witness_path))
        errors.extend(field_witness_graph_errors(field_witness))
        if field_witness is not None:
            errors.extend(compare_visible_to_field_witness(witness, field_witness))
    return summary_from_visible(witness, errors), 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_positional", nargs="?", type=Path, help="Markdown/text witness or field_witness JSON")
    parser.add_argument("--input", dest="input_named", type=Path, help="Markdown/text witness or field_witness JSON")
    parser.add_argument("--field-witness", type=Path, help="Optional field_witness JSON to compare with visible text")
    parser.add_argument("--out", type=Path, help="Write visualization to this path (.html or .md)")
    parser.add_argument("--json-out", type=Path, help="Write parsed JSON summary to this path")
    args = parser.parse_args()

    input_path = args.input_named or args.input_positional
    if input_path is None and args.field_witness is not None:
        input_path = args.field_witness
    if input_path is None:
        parser.error("provide an input path")
    field_witness_path = None if input_path == args.field_witness else args.field_witness
    payload, status = payload_from_input(input_path, field_witness_path)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if args.out.suffix.lower() == ".html":
            args.out.write_text(render_html(input_path, payload), encoding="utf-8")
        else:
            args.out.write_text(render_markdown(input_path, payload), encoding="utf-8")
        print(f"closure witness visualization written: {args.out}")
        json_out = args.json_out or args.out.with_suffix(".json")
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"closure witness JSON summary written: {json_out}")
    elif args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"closure witness JSON summary written: {args.json_out}")
    else:
        print(render_markdown(input_path, payload))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
