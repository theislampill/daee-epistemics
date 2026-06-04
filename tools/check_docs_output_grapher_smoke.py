#!/usr/bin/env python3
"""Smoke the docs Output Grapher JavaScript over a governed output.

This is a docs/public visualization smoke, not proof authority. Checker-owned
Stage 08 sidecars remain the proof gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DOCS_GRAPHER_JS = ROOT / "docs" / "index" / "output-grapher.js"
DEFAULT_OUTPUT = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "cases"
    / "staged-a9-science-source-proofbundle"
    / "output.md"
)


NODE_RUNNER = r"""
const fs = require('fs');
const vm = require('vm');

const [jsPath, outputPath, witnessPath, certificatePath] = process.argv.slice(2);
const source = fs.readFileSync(jsPath, 'utf8');
const output = fs.readFileSync(outputPath, 'utf8');
const witness = witnessPath ? fs.readFileSync(witnessPath, 'utf8') : '';
const certificate = certificatePath ? fs.readFileSync(certificatePath, 'utf8') : '';

function inertElement() {
  return {
    style: {},
    dataset: {},
    classList: { add(){}, remove(){}, contains(){ return false; } },
    setAttribute(){},
    getAttribute(){ return null; },
    appendChild(){},
    insertBefore(){},
    remove(){},
    click(){},
    addEventListener(){},
    querySelector(){ return null; },
    querySelectorAll(){ return []; },
    cloneNode(){ return inertElement(); },
    ownerSVGElement: null,
    viewBox: { baseVal: { width: 0, height: 0 } },
    width: { baseVal: { value: 0 } },
    height: { baseVal: { value: 0 } },
    innerHTML: '',
    textContent: ''
  };
}

const document = {
  body: { appendChild(){} },
  addEventListener(){},
  getElementById(){ return null; },
  createElement(){ return inertElement(); },
  createElementNS(){ return inertElement(); },
  querySelector(){ return null; },
  querySelectorAll(){ return []; }
};
const window = { document };
const context = {
  console,
  window,
  document,
  Blob,
  URL: {
    createObjectURL(){ return 'blob:docs-output-grapher-smoke'; },
    revokeObjectURL(){}
  },
  TextEncoder,
  TextDecoder,
  setTimeout,
  clearTimeout
};
context.globalThis = context;
vm.runInNewContext(source, context, { filename: jsPath });

const api = context.window.daeeOutputGrapher;
const failures = [];
if (!api) failures.push('window.daeeOutputGrapher missing');
if (api && typeof api.parseOutput !== 'function') failures.push('parseOutput export missing');
if (api && typeof api.renderGraph !== 'function') failures.push('renderGraph export missing');

let model = null;
let svg = '';
if (!failures.length) {
  model = api.parseOutput(output, witness, certificate);
  svg = api.renderGraph(model);
}

const sections = model?.sourceSections || [];
const finalOrder = sections
  .filter(section => ['restorative_response', 'closing_formulation', 'closure_witness'].includes(section.type))
  .map(section => section.type);
const jsonText = model ? JSON.stringify(model) : '';
const warnings = model ? [...(model.warnings || []), ...(model.witnessMismatches || [])] : [];
const result = {
  inputBytes: Buffer.byteLength(output),
  hasApi: Boolean(api),
  nodeCount: model ? Object.keys(model.nodes || {}).length : 0,
  edgeCount: model ? (model.edges || []).length : 0,
  errors: model ? (model.errors || []) : [],
  warningCount: warnings.length,
  bodyChars: model ? (model.zones?.bodyProse || '').length : 0,
  closureChars: model ? (model.zones?.closureWitness || '').length : 0,
  embeddedFieldWitness: Boolean(model?.witnessSources?.embedded),
  restorativeChars: model ? (model.restorativeResponse || '').length : 0,
  closingChars: model ? (model.closingFormulation || '').length : 0,
  finalOrder,
  svgBytes: Buffer.byteLength(svg),
  jsonBytes: Buffer.byteLength(jsonText),
  svgHasPrimaryMap: svg.includes('<svg id="ogSvg"') && svg.includes('Restorative noetic map infographic'),
  svgHasRestorativeCard: svg.includes('outputGrapherRestorativeResponse'),
  svgHasClosingCard: svg.includes('outputGrapherClosingFormulation'),
  svgHasClosureWitnessCard: svg.includes('outputGrapherClosureWitnessSource'),
  exportedApi: {
    png: typeof api?.exportPng === 'function',
    sectionZip: typeof api?.exportPngSections === 'function',
    svg: typeof api?.exportSvg === 'function',
    json: typeof api?.exportJson === 'function',
    sectionPlan: typeof api?.sectionExportPlan === 'function'
  }
};

if (!model) failures.push('parseOutput did not return a model');
else {
  if (result.errors.length) failures.push(`parser hard errors: ${result.errors.join('; ')}`);
  if (result.nodeCount < 4) failures.push(`too few graph nodes: ${result.nodeCount}`);
  if (result.edgeCount < 1) failures.push(`too few graph edges: ${result.edgeCount}`);
  if (result.bodyChars < 1000) failures.push(`visible body prose not separated: ${result.bodyChars}`);
  if (result.closureChars < 100) failures.push(`Closure/Reconstruction Witness not detected: ${result.closureChars}`);
  if (!result.embeddedFieldWitness) failures.push('embedded field_witness not detected');
  if (result.restorativeChars < 40) failures.push(`Restorative Response not detected: ${result.restorativeChars}`);
  if (result.closingChars < 40) failures.push(`Closing Formulation not detected: ${result.closingChars}`);
  if (result.finalOrder.join('>') !== 'restorative_response>closing_formulation>closure_witness') {
    failures.push(`wrong final section order: ${result.finalOrder.join('>')}`);
  }
  if (!result.svgHasPrimaryMap) failures.push('primary SVG map not generated');
  if (!result.svgHasRestorativeCard) failures.push('Restorative Response card missing from SVG');
  if (!result.svgHasClosingCard) failures.push('Closing Formulation card missing from SVG');
  if (!result.svgHasClosureWitnessCard) failures.push('Closure/Reconstruction Witness card missing from SVG');
  if (result.jsonBytes < 1000) failures.push('JSON export payload too small');
  if (result.svgBytes < 1000) failures.push('SVG export payload too small');
  for (const [key, present] of Object.entries(result.exportedApi)) {
    if (!present) failures.push(`${key} export API missing`);
  }
}

process.stdout.write(JSON.stringify({ verdict: failures.length ? 'FAIL' : 'PASS', failures, result }, null, 2));
process.exit(failures.length ? 1 : 0);
"""


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def existing_file(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"{label} does not exist: {path}")
    return resolved


def run_smoke(output: Path, witness: Path | None, certificate: Path | None) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        raise SystemExit("node is required for docs Output Grapher JavaScript smoke")
    output = existing_file(output, "output")
    if witness is not None:
        witness = existing_file(witness, "field_witness")
    if certificate is not None:
        certificate = existing_file(certificate, "collapse certificate")
    if not DOCS_GRAPHER_JS.is_file():
        raise SystemExit(f"docs Output Grapher JS missing: {rel(DOCS_GRAPHER_JS)}")

    with tempfile.TemporaryDirectory(prefix="docs-output-grapher-smoke-") as raw_tmp:
        runner = Path(raw_tmp) / "runner.cjs"
        runner.write_text(NODE_RUNNER, encoding="utf-8")
        command = [
            node,
            str(runner),
            str(DOCS_GRAPHER_JS),
            str(output),
            str(witness) if witness is not None else "",
            str(certificate) if certificate is not None else "",
        ]
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        detail = proc.stdout.strip() or proc.stderr.strip()
        raise SystemExit(f"docs Output Grapher smoke failed for {rel(output)}:\n{detail}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"docs Output Grapher smoke emitted invalid JSON: {exc}\n{proc.stdout}") from exc
    if payload.get("verdict") != "PASS":
        raise SystemExit(f"docs Output Grapher smoke failed for {rel(output)}:\n{json.dumps(payload, indent=2)}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Full daee-epistemics output Markdown to smoke. Defaults to a retained proof-owned docs-grapher case.",
    )
    parser.add_argument("--field-witness", type=Path, help="Optional separate field_witness JSON.")
    parser.add_argument("--certificate", type=Path, help="Optional collapse certificate JSON.")
    parser.add_argument(
        "--require-explicit-output",
        action="store_true",
        help="Fail unless --output was explicitly supplied. Use for exact fresh Stage 07 output readiness gates.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON smoke payload.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.require_explicit_output and args.output is None:
        raise SystemExit(
            "docs Output Grapher exact-output smoke requires --output; "
            "the retained default fixture is not enough for a fresh Stage 07 artifact"
        )
    output = args.output or DEFAULT_OUTPUT
    payload = run_smoke(output, args.field_witness, args.certificate)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        result = payload["result"]
        print("docs Output Grapher smoke: PASS")
        print(f"output: {rel(output)}")
        print(
            "parsed: "
            f"nodes={result['nodeCount']} edges={result['edgeCount']} "
            f"body_chars={result['bodyChars']} closure_chars={result['closureChars']} "
            f"restorative_chars={result['restorativeChars']} closing_chars={result['closingChars']}"
        )
        print(f"final_section_order: {' -> '.join(result['finalOrder'])}")
        print(
            "generated: "
            f"svg_bytes={result['svgBytes']} json_bytes={result['jsonBytes']} "
            f"export_api={','.join(key for key, value in result['exportedApi'].items() if value)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
