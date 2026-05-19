#!/usr/bin/env python3
"""Render a Closure/Reconstruction Witness as JSON plus Mermaid.

The output is a research/evaluation artifact. It visualizes rendered coverage
structure; it does not prove live noetic competence.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from closure_witness_lib import (
    ALLOWED_TERMINAL_STATES,
    closure_witness_errors,
    parse_closure_witness,
)


CLASS_BY_STATE = {
    "landed": "landed",
    "discharged-as-derivative": "discharged",
    "held-with-reason": "held",
    "carried-PARTIAL": "carried",
    "carried-RECURSE": "carried",
    "cleared": "cleared",
}


def mermaid_escape(value: str) -> str:
    return value.replace('"', "'").replace("\n", "<br/>")


def node_label(burden: str, state: str, detail: str) -> str:
    if detail:
        return f'{burden}["{burden}<br/>{mermaid_escape(state)}<br/>{mermaid_escape(detail[:80])}"]'
    return f'{burden}["{burden}<br/>{mermaid_escape(state)}"]'


def render_mermaid(witness) -> str:  # noqa: ANN001
    burdens = list(dict.fromkeys(witness.initial_burdens + list(witness.terminal_states)))
    for src, target in witness.edges:
        if src not in burdens:
            burdens.append(src)
        if target not in burdens:
            burdens.append(target)
    lines = [
        "```mermaid",
        "flowchart TD",
        "  classDef landed fill:#b7f7c1,stroke:#227a3a,color:#111;",
        "  classDef discharged fill:#b9dcff,stroke:#2c5f91,color:#111;",
        "  classDef held fill:#fff2a8,stroke:#8a6d00,color:#111;",
        "  classDef carried fill:#ffd1a8,stroke:#9a4f00,color:#111;",
        "  classDef cleared fill:#d8f5e4,stroke:#3c7d55,color:#111;",
        "  classDef missing fill:#ffc4c4,stroke:#a00000,color:#111;",
    ]
    for burden in burdens:
        payload = witness.terminal_states.get(burden)
        if payload:
            state = payload["state"]
            detail = payload["detail"]
        else:
            state = "missing terminal state"
            detail = ""
        lines.append("  " + node_label(burden, state, detail))
    for src, target in witness.edges:
        lines.append(f"  {src} --> {target}")
    for burden in burdens:
        payload = witness.terminal_states.get(burden)
        class_name = "missing" if payload is None else CLASS_BY_STATE.get(payload["state"], "missing")
        lines.append(f"  class {burden} {class_name};")
    lines.append("```")
    return "\n".join(lines)


def summary_payload(witness, errors: list[str]) -> dict:  # noqa: ANN001
    burdens = list(dict.fromkeys(witness.initial_burdens + list(witness.terminal_states)))
    for src, target in witness.edges:
        if src not in burdens:
            burdens.append(src)
        if target not in burdens:
            burdens.append(target)
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
        "initial_burden_set": witness.initial_burdens,
        "terminal_states": witness.terminal_states,
        "nodes": nodes,
        "edges": [{"from": src, "to": target, "kind": "depends-on"} for src, target in witness.edges],
        "roots": witness.roots,
        "parallel": [{"a": a, "b": b} for a, b in witness.parallel],
        "divergence": witness.divergence,
        "curl": witness.curl,
        "coverage_complete": witness.coverage_complete,
        "collapse_positive": witness.collapse_positive,
        "errors": errors,
    }


def render_markdown(path: Path, witness, errors: list[str]) -> str:  # noqa: ANN001
    payload = summary_payload(witness, errors)
    return "\n".join(
        [
            "# Closure Witness Visualization",
            "",
            f"Source: `{path.as_posix()}`",
            "",
            f"- coverage_complete: `{str(witness.coverage_complete).lower()}`",
            f"- collapse_positive: `{str(witness.collapse_positive).lower()}`",
            f"- ∇·B: `{witness.divergence or 'missing'}`",
            f"- ∇×κ: `{witness.curl or 'missing'}`",
            "",
            "## Mermaid DAG",
            "",
            render_mermaid(witness),
            "",
            "## Parsed JSON",
            "",
            "```json",
            json.dumps(payload, indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Markdown/text file containing a Closure/Reconstruction Witness")
    parser.add_argument("--out", type=Path, help="Write Markdown visualization to this path")
    parser.add_argument("--json-out", type=Path, help="Write parsed JSON summary to this path")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    witness = parse_closure_witness(text)
    if witness is None:
        print(f"{args.input}: missing Closure/Reconstruction Witness block")
        return 1
    errors = closure_witness_errors(witness)
    output = render_markdown(args.input, witness, errors)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"closure witness visualization written: {args.out}")
        json_out = args.json_out or args.out.with_suffix(".json")
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(summary_payload(witness, errors), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"closure witness JSON summary written: {json_out}")
    elif args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary_payload(witness, errors), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"closure witness JSON summary written: {args.json_out}")
    else:
        print(output)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
