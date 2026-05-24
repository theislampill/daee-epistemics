#!/usr/bin/env python3
"""Validate the docs Output Collapse Grapher artifact and fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from output_grapher_lib import burden_token, extract_embedded_field_witness, graph_html, parse_output, result_summary

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"
MANIFEST = ROOT / "docs" / "index" / "manifest.json"
SECTION = ROOT / "docs" / "index" / "sections" / "output-grapher.html"
JS = ROOT / "docs" / "index" / "output-grapher.js"
CSS = ROOT / "docs" / "index" / "output-grapher.css"
FIXTURE_ROOT = ROOT / "tests" / "docs-output-grapher"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def expected_mode(text: str, path: Path) -> str:
    match = re.search(r"<!--\s*expect:\s*(pass|fail|warn)\s*-->", text)
    if match:
        return match.group(1)
    name = path.name
    if name.startswith("valid-"):
        return "pass"
    if name.startswith("invalid-legacy-notation-warning"):
        return "warn"
    if name.startswith("invalid-"):
        return "fail"
    return "pass"


def warning_failures(warnings: list[str]) -> list[str]:
    return [f"warning treated as proof-mode failure: {warning}" for warning in warnings]


def check_static_artifact(errors: list[str]) -> None:
    for path in (MANIFEST, SECTION, JS, CSS):
        if not path.exists():
            errors.append(f"{rel(path)} is missing")
    if errors:
        return
    index_text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    section_text = SECTION.read_text(encoding="utf-8")
    js_text = JS.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")
    combined = "\n".join([manifest_text, section_text, js_text, css_text, index_text])

    required = {
        "manifest tab": '"id": "output-grapher"',
        "tab label": "Output Grapher",
        "section source": "docs/index/sections/output-grapher.html",
        "local JS": "index/output-grapher.js",
        "local CSS": "index/output-grapher.css",
        "export PNG button": "ogExportPngBtn",
        "sectioned PNG button": "ogExportPngSectionsBtn",
        "section ZIP button label": "Export section ZIP",
        "export PNG size selector": "ogExportWidthMode",
        "desktop PNG mode": "Desktop PNG (1800px)",
        "poster PNG mode": "Poster PNG (2200px)",
        "compact PNG mode": "Compact PNG (1500px)",
        "export SVG button": "ogExportSvgBtn",
        "export JSON button": "ogExportJsonBtn",
        "optional Mermaid export": "Export Mermaid",
        "optional Mermaid ELK": "defaultRenderer': 'elk",
        "full output input label": "Paste full daee-epistemics output",
        "full output input subtitle": "The grapher will separate the readable response, closure witness, and field_witness automatically.",
        "advanced field witness disclosure": "Advanced: separate field_witness JSON",
        "optional separate witness label": "Optional separate field_witness JSON",
        "optional separate witness help": "Use only if your field_witness is in a separate JSON block or file",
        "primary map view label": "Restorative Noetic Map View",
        "map scope support": "What the Restorative Noetic Map shows",
        "input ontology scope": "ontological noetic structure",
        "MRP outcome scope": "MRP result type",
        "restoration aim scope": "restoration aim",
        "show validation details control": "Show validation details",
        "show technical details control": "Show technical details",
        "input digest panel": "Reply / Claim Being Rejected",
        "reader-facing input fallback": "readerInputDigest",
        "plain dependency panel": "What The Reply Depends On",
        "burden inventory panel": "Main Problems In The Reply",
        "collapse status panel": "Final Answer From The Output",
        "graph conclusion card": "Final Answer From The Output",
        "plain restoration summary": "Restoration Summary",
        "restorative noetic title": "Output grapher — Restorative Noetic Map",
        "large case headline": "storyCaseHeadline",
        "generic prooftext/source-reading headline": "CASE: prooftext / source-reading reply",
        "restoration bullet builder": "restorationBullets",
        "formal case fill": "Formal Case Fill",
        "formal case fill renderer": "renderFormalCaseFill",
        "story view renderer": "renderStorySvg",
        "story view default technical appendix": "renderStorySvg(model,{includeTechnicalAppendix:true})",
        "story burden cards": "outputGrapherStoryBurden",
        "plain claim label": "Reply / claim being rejected",
        "plain conclusion label": "Final Answer From The Output",
        "plain dependency label": "What the reply depends on",
        "baseline ledger parser": "B_LA",
        "generated ledger parser": "B_MRP",
        "baseline-only main problems note": "Baseline only: this section lists B_LA",
        "generated follow-up panel": "Preempted Problems Surfaced By Reread",
        "generated follow-up story card": "Preempted problems surfaced by reread",
        "route gradient parser": "Route-gradient",
        "del-dot parser": "del-dot",
        "del-cross parser": "del-cross",
        "collapsed top help": "outputGrapherHelp",
        "top help summary": "How to read this",
        "top help technical labels": "Land(¹B)",
        "body prose split": "splitOutputZones",
        "embedded field witness extraction": "extractEmbeddedFieldWitness",
        "embedded/separate witness comparison": "compareEmbeddedAndSeparateWitness",
        "field witness edge comparison": "edge mismatch visible=",
        "visible final section extractor": "extractBodySection",
        "visible source-section detector": "detectSourceSections",
        "source-section render manifest": "sourceCoverageManifest",
        "section source coverage manifest": "sourceCoverage",
        "source setup card renderer": "outputGrapherSourceSetup",
        "source-section render layer classifier": "sourceRenderLayer",
        "technical source coverage appendix": "outputGrapherSourceCoverageAppendix",
        "closure witness source renderer": "outputGrapherClosureWitnessSource",
        "visible final prose cleaner": "cleanVisibleProseBlock",
        "visible body extraction": "bodyExtract",
        "body-first canonicalizer": "canonicalizePublicNotation",
        "body submove detail extraction": "submoveDetails",
        "body submove resolver": "bodySubmoveLabel",
        "body submove section resolver": "bodySubmoveSections",
        "submove section renderer": "renderSubmoveSections",
        "final body prose renderer": "renderFinalProseCard",
        "restorative response card": "outputGrapherRestorativeResponse",
        "closing formulation card": "outputGrapherClosingFormulation",
        "shared SVG header component": "function renderCardHeader",
        "shared SVG header badges": "function renderHeaderBadges",
        "pixel-estimated SVG text width": "function estimateSvgTextWidth",
        "shared SVG text wrapper": "function wrapSvgText",
        "story pixel wrapper": "function storyWrap",
        "body-first land panel": "bodyLandText",
        "body-first reread panel": "bodyRereadText",
        "route panel resolver": "routePanelItems",
        "structured MRP rows": "mrpPanelRows",
        "baseline label resolver": "baselineBurdenLabels",
        "generated label resolver": "generatedBurdenLabels",
        "accounted summary resolver": "accountedBurdenLabels",
        "generated burden mass flag": "mass-insufficient",
        "operation-shaped guard": "conclusion-shaped rather than operation-shaped",
        "MRP key-value renderer": "storyKeyValueBlock",
        "list-like remaining rendering": "splitListLikeItems",
        "plain answer label": "How this problem is answered",
        "plain land label": "What this establishes",
        "plain reread label": "After this, what remains?",
        "plain MRP label": "Follow-up: pressure-check",
        "burden cluster container": "outputGrapherBurdenCluster",
        "semantic edge labels": "outputGrapherEdgeLabel",
        "generated burden relation": "new problem surfaced",
        "closure restoration edge": "closure / restoration",
        "inline SVG renderer": "renderGraph",
        "PNG export function": "exportPng",
        "sectioned PNG export function": "exportPngSections",
        "section ZIP creator": "createZipBlob",
        "section PNG renderer": "renderPngBlobFromSvgNode",
        "section export manifest": "sectionExportManifest",
        "semantic intro section anchor": "data-og-section=\"intro\"",
        "semantic burden section anchor": "data-og-section=\"burden\"",
        "semantic restoration section anchor": "data-og-section=\"restoration\"",
        "semantic formal section anchor": "data-og-section=\"formal\"",
        "semantic section collector": "storySemanticSections",
        "bounded section crop": "boundedSectionCrop",
        "section crop previous boundary": "previousSectionBottom",
        "section crop next boundary": "nextSectionTop",
        "foreign section overlap flag": "foreignSectionOverlap",
        "section canvas safety flag": "canvasSafe",
        "section planned PNG safety": "plannedPng",
        "sectioned export aggregate safety": "sectionedCanvasSafe",
        "font-ready section export wait": "waitForExportLayout",
        "section export plan API": "sectionExportPlan",
        "section ZIP filename": "daee-output-grapher-sections.zip",
        "intro section filename": "01-intro-case-and-verdict.png",
        "restoration section filename": "restoration-summary.png",
        "formal section filename": "formal-reconstruction.png",
        "export coverage report": "exportCoverageReport",
        "restorative export coverage": "hasRestorativeResponse",
        "closing export coverage": "hasClosingFormulation",
        "formal export coverage": "hasFormalCaseFill",
        "top-right route badge": 'data-route-badge-position="top-right"',
        "top-right shared badges": "renderHeaderBadges(badgeItems,x+pad,badgeY,contentW,'right')",
        "padded export clone": "cloneSvgForExport",
        "canonical burden": "¹B",
        "canonical submove": "¹B₁",
        "MRP node": "MRP(ⁿB)",
        "canonical edge": "ⁿB → ⁿ⁺¹B",
        "restoration orientation": "N_fiṭrī",
        "field witness": "field_witness",
        "route type generated": "generated_burden_instantiation",
        "route type held": "held_burden_activation",
        "route type no-new": "no_new_resultant",
        "route type hold partial": "hold_partial",
        "route type loopbreak": "loopbreak",
        "terminal route STOP": "STOP / closure as licensed.",
    }
    for label, token in required.items():
        if token not in combined:
            errors.append(f"Output Grapher missing {label}: {token!r}")

    forbidden = ("https://", "unpkg.com", "cdn.jsdelivr", "cdnjs")
    for path, text in ((SECTION, section_text), (JS, js_text), (CSS, css_text)):
        text_without_svg_namespace = text.replace("http://www.w3.org/2000/svg", "")
        for token in forbidden:
            if token in text_without_svg_namespace:
                errors.append(f"{rel(path)} contains forbidden external dependency token {token!r}")
        if "http://" in text_without_svg_namespace:
            errors.append(f"{rel(path)} contains forbidden external dependency token 'http://'")
    if "mermaid" in js_text.lower() and "optional" not in section_text.lower():
        errors.append("Mermaid may only be optional/lossy; primary renderer must be inline SVG/HTML")
    if "<svg" not in js_text or ("<line" not in js_text and "<path" not in js_text) or "<rect" not in js_text:
        errors.append("Output Grapher primary renderer must build exportable inline SVG geometry")
    if "burden-submove" not in js_text or "model.submoves[b]" not in js_text:
        errors.append("Output Grapher must assign submoves to parent burden clusters")
    if "MRP(" not in js_text or "resultTypes" not in js_text:
        errors.append("Output Grapher must display MRP result types")
    forbidden_public_patterns = {
        "raw failure-point issue labels": "function issueLabel(b){return `Failure point",
        "raw B fallback in inventory": "model.nodes[b]?.label||b",
        "old hyphen issue title": "${issueLabel(b)} - ",
        "repeated story badge chrome": "parts.push(storyBadge",
        "empty route panel rendering": "storySectionBlock('Next issue / closure',humanize(routes)",
        "field witness as body copy": "field_witness metadata appears as main",
        "density view controls": "data-og-density",
        "density-mode state": "currentDensity",
        "density config": "densityConfig",
        "hidden submove count": "hiddenCount",
        "visible submove slice": "visibleSms",
        "sentence-limited submove prose": "firstSentences",
        "decorative accent helper": "accentSvg",
        "decorative top accent rectangle": 'height="3" fill=',
        "paint-stroke accent": "stroke-linecap",
        "character-count story wrapper": "function storyLineChars",
        "old width-to-character story wrapping": "width/(size*",
        "inspector truncation marker": "(more in inspector)",
        "old story title": "OUTPUT GRAPHER - REBUTTAL MAP",
        "long land panel title": "What this establishes against the reply",
        "long reread panel title": "After this answer, what remains?",
        "long MRP panel title": "Follow-up: does the reply still have pressure?",
        "left route badge text column": "textX=x+pad+badgeW+22",
        "in-flow reader guide title": "How to read this map",
        "obsolete reader guide renderer": "function readingGuideItems",
        "technical proof strip inside restoration": "Technical proof strip",
        "old plain-language view label": "Plain-language Rebuttal View",
        "old technical pipeline view label": "Technical Pipeline View",
        "old validation view label": "Validation View",
        "prominent mode button container": "outputGrapherModes",
        "mode button data attribute": "data-og-mode",
        "loose section PNG downloads": "downloadBlob(name,'image/png',png)",
        "old sectioned PNG label": "Export Sectioned PNG",
        "duplicate Land technical line": "technical:`Land(${b})`",
        "duplicate reread technical line": "technical:'R(H,Δ)'",
    }
    for label, token in forbidden_public_patterns.items():
        if token in js_text:
            errors.append(f"Output Grapher still has {label}: {token!r}")
    if "bodyExtract.burdenTitles" not in js_text or "bodyExtract.submoveDetails" not in js_text:
        errors.append("Output Grapher must resolve burden/submove display text from visible body prose before witness metadata")
    if "canonicalizePublicNotation(edgeText)" not in js_text:
        errors.append("Output Grapher must canonicalize public graph/resultant text before rendering")
    if "Move to next identified problem:" not in js_text or "Why closure is withheld:" not in js_text:
        errors.append("Output Grapher route panel must name the next burden and explain why closure is withheld")
    if "Target', details.target" not in js_text or "Result', details.result" not in js_text or "Contribution-to-Land', details.contribution" not in js_text or "TTP operation body', details.body" not in js_text:
        errors.append("Output Grapher submove cards must render body-derived target/operation-body/result/contribution details")
    if "labelSize" not in js_text or "bodySize" not in js_text or "font-weight" not in js_text:
        errors.append("Output Grapher submove cards must use differentiated label/body typography")
    if "['Graph movement', graph]" not in js_text or "['Route', route]" not in js_text:
        errors.append("Output Grapher MRP panel must render structured graph movement and route rows")
    if "cloneSvgForExport(svg)" not in js_text or "viewBox',`${-padding}" not in js_text:
        errors.append("Output Grapher exports must use a padded full-viewBox SVG clone")
    if "Main Problems In The Reply" in combined and "bodyBurdenDescription(model,b)" not in js_text:
        errors.append("Output Grapher burden inventory must use visible body headings, not witness-only labels")
    check_submove_content_preservation(js_text, errors)
    check_generated_burden_render_shape(errors)
    check_restoration_summary_count_consistency(errors)
    check_source_section_preservation(errors)
    check_single_paste_embedded_witness(errors)
    check_browser_formal_reread_state_comparison(errors)
    check_paired_parser_alias_cleanup(errors)


def check_paired_parser_alias_cleanup(errors: list[str]) -> None:
    source = """
daee-epistemics — NOETIC FIELD EXECUTION
Layer A
Initial burden set: [¹B, ²B]

## Burden 1 / ¹B — root pressure
Land(¹B): landed.

[Mid-Reread Pressure]
Target: ¹B / root pressure
R(H,Δ): held routes rechecked: ²B from Initial burden set; live remainder: downstream pressure; release/next: release ²B
Field diagnostics: ∇·B: non-neutral / ²B / B2 carried-PARTIAL; ∇×κ: non-null / ²B loop target
Landed delta: Delta(B1) / Δ¹B and Δκ: root pressure landed
Route-gradient: already-held ²B / B2 from Initial burden set / B_LA; Delta(B1) leaves downstream pressure live; release ²B
Finding: genuine-dependent
MRP route result type: held_burden_activation
MRP resultant: genuine-dependent -> release ²B
Graph delta: ¹B → ²B
Route: RECURSE

Closure/Reconstruction Witness
Initial burden set: [¹B, ²B]
Terminal states:
¹B: landed
²B: landed
Burden dependency graph:
¹B (root) → ²B

field_witness
{"B_LA":["B1","B2"],"B_MRP":[],"B_total":["B1","B2"],"nodes":["B1","B2"],"edges":[{"from":"B1","to":"B2","type":"held_burden_activation"}],"mrp_resultants":[{"source":"B1","type":"held_burden_activation","graph":"B1 → B2","route":"RECURSE"}],"terminal_states":{"B1":"landed","B2":"landed"}}
"""
    parsed = parse_output(source)
    legacy_warnings = [warning for warning in parsed.warnings if "parsed legacy alias B" in warning]
    if legacy_warnings:
        errors.append(f"paired canonical/parser aliases should not warn: {legacy_warnings}")
    if burden_token(2) not in parsed.burdens:
        errors.append("paired parser alias cleanup must keep canonical burden parsing intact")

    bad = parse_output(
        """
NOETIC FIELD EXECUTION
Layer A
Initial burden set: [B1]

Closure/Reconstruction Witness
Terminal states:
B1: landed
Burden dependency graph:
B1 (root)
"""
    )
    if not any("parsed legacy alias B1" in warning for warning in bad.warnings):
        errors.append("unpaired public ASCII burden IDs must still warn as legacy aliases")


def check_single_paste_embedded_witness(errors: list[str]) -> None:
    source = """
NOETIC FIELD EXECUTION
Layer A
initial burden inventory: B1

## Burden 1: body burden survives as the visible source
B1_1[definition-discipline] - answer the visible problem.
Land(B1): the body burden lands.
R(H,Delta): no further pressure remains.
MRP(B1): stable
Route: STOP

Closure/Reconstruction Witness
coverage_complete=true

field_witness
{"nodes":["B1"],"edges":[],"ledger":{"B_LA":["B1"],"B_MRP":[],"B_total":["B1"]},"mrp_resultants":[{"source":"B1","type":"no_new_resultant","graph":null,"route":"STOP"}],"terminal_states":{"B1":"landed"}}
"""
    result = parse_output(source)
    if result.errors:
        errors.append(f"single pasted output with embedded field_witness should parse without errors: {result.errors}")
    disagreed = parse_output(source, '{"nodes":["B2"],"edges":[]}')
    if not any("embedded field_witness and separate field_witness disagree" in error for error in disagreed.errors):
        errors.append("separate field_witness JSON must be compared against embedded field_witness and fail on disagreement")
    if burden_token(1) not in disagreed.body_burdens:
        errors.append("visible body burden set must remain separate from field_witness structural nodes")
    if burden_token(2) in disagreed.body_burdens:
        errors.append("visible body burden set must stop before closure witness / field_witness structural nodes")
    edge_disagreed = parse_output(source, '{"nodes":["B1"],"edges":[["B1","B1"]]}')
    if not any("edge mismatch visible=" in error for error in edge_disagreed.errors):
        errors.append("field_witness edge mismatches must fail, not only report node mismatches")
    array_terminal_source = source.replace(
        '"terminal_states":{"B1":"landed"}',
        '"terminal_states":[{"id":"B1","notation":"¹B","state":"landed"}]',
    )
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
eval(fs.readFileSync({json.dumps(str(JS))}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput({json.dumps(array_terminal_source)}, '');
console.log(JSON.stringify({{errors: model.errors || []}}));
"""
    browser = subprocess.run(
        ["node", "-e", node_script],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    if browser.returncode != 0:
        errors.append(f"browser embedded field_witness terminal-array check could not run: {(browser.stderr or browser.stdout).strip()}")
    else:
        parsed = json.loads(browser.stdout or "{}")
        if parsed.get("errors"):
            errors.append(f"browser embedded field_witness terminal-array check failed: {parsed['errors']}")


def check_browser_formal_reread_state_comparison(errors: list[str]) -> None:
    source = """
NOETIC FIELD EXECUTION
Layer A
Initial burden set: B1

## Burden 1 / B1: root pressure
B1_1[M1] - repair the root pressure.
Land(B1): root pressure repaired.

[Mid-Reread Pressure]
Target: B1 / root pressure
R(H,Delta): live remainder none; release/next STOP
Route-gradient: STOP after B1
Finding: stable
MRP route result type: no_new_resultant
MRP resultant: stable -> no new graph edge; STOP
Graph delta: none
Route: STOP

Closure/Reconstruction Witness
coverage_complete=true
Terminal states:
B1: landed / M1 / root pressure repaired
Burden dependency graph: B1 (root)

field_witness
{"nodes":["B1"],"edges":[],"ledger":{"B_LA":["B1"],"B_MRP":[],"B_total":["B1"]},"mrp_resultants":[{"source":"B1","type":"no_new_resultant","graph":"none","route":"STOP"}],"formal_reread_states":[{"source_burden":"B1","route_result_type":"no_new_resultant","graph_delta":"none","route":"HOLD"}],"terminal_states":{"B1":"landed"}}
"""
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
eval(fs.readFileSync({json.dumps(str(JS))}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput({json.dumps(source)}, '');
console.log(JSON.stringify({{errors: model.errors || []}}));
"""
    browser = subprocess.run(
        ["node", "-e", node_script],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    if browser.returncode != 0:
        errors.append(f"browser formal_reread_states check could not run: {(browser.stderr or browser.stdout).strip()}")
        return
    try:
        parsed = json.loads(browser.stdout or "{}")
    except json.JSONDecodeError as exc:
        errors.append(f"browser formal_reread_states check emitted invalid JSON: {exc}")
        return
    found = [str(item) for item in parsed.get("errors", [])]
    if not any("formal_reread_states[1]" in item and "route mismatch" in item for item in found):
        errors.append("browser parser must reject field_witness.formal_reread_states route mismatch")


def parse_skill_output_with_browser_js(path: Path) -> dict[str, list[str]]:
    """Run the browser-side parser so --skill-output cannot miss JS-only failures."""

    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
eval(fs.readFileSync({json.dumps(str(JS))}, 'utf8'));
const source = fs.readFileSync({json.dumps(str(path))}, 'utf8');
const model = window.daeeOutputGrapher.parseOutput(source, '');
console.log(JSON.stringify({{errors: model.errors || [], warnings: model.warnings || []}}));
"""
    result = subprocess.run(
        ["node", "-e", node_script],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        return {"errors": [f"browser Output Grapher parser failed to run: {(result.stderr or result.stdout).strip()}"], "warnings": []}
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        return {"errors": [f"browser Output Grapher parser emitted invalid JSON: {exc}"], "warnings": []}
    return {
        "errors": [str(item) for item in parsed.get("errors", [])],
        "warnings": [str(item) for item in parsed.get("warnings", [])],
    }


def check_submove_content_preservation(js_text: str, errors: list[str]) -> None:
    fixture = r'''
NOETIC FIELD EXECUTION
Layer A
- read status: A claim moves a source sentence away from its actual subject.
initial burden inventory: B1

## Burden 1: the source sentence is being moved away from its subject
B1_1[definition-discipline] — restore the proposition actually uttered
Target: the exact sentence under dispute and the addressed subject named inside it.
What it does: restores the sentence under dispute before a later model is allowed to rewrite its grammar.
Result: the reply can no longer test the sentence by moving a key term into a manufactured formula.
Contribution-to-Land(B1): the subject-predicate relation is restored and the imported formula loses authority.

Land(B1): the source sentence is restored against the imported formula.
R(H,Delta): no downstream problem remains in this reduced fixture.
MRP(B1): stable
MRP resultant: stable; graph=none; route=STOP
Route: STOP

Restorative Response

The source sentence is restored, and the reply no longer controls the conclusion by moving the wording into a later formula.

Closing Formulation

The claim fails because its imported formula does not answer the sentence as given.

Closure/Reconstruction Witness
coverage_complete=true
∇·B: neutral
∇×κ: null
𝒞(Ψᴺ): coverage_complete=true
'''
    required_fragments = [
        "Target:",
        "the exact sentence under dispute",
        "What it does:",
        "restores the sentence under dispute",
        "Result:",
        "the reply can no longer test the sentence",
        "Contribution-to-Land:",
        "the subject predicate relation is restored",
        "Restorative Response",
        "The source sentence is restored",
        "Closing Formulation",
        "The claim fails because its imported formula",
    ]
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
const source = {fixture!r};
eval(fs.readFileSync({str(JS)!r}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput(source, '');
const svg = window.daeeOutputGrapher.renderGraph(model);
const required = {required_fragments!r};
const missing = required.filter(token => !svg.includes(token));
const forbidden = ['height="3" fill=', 'stroke-linecap', '(more in inspector)', '...'];
const forbiddenHits = forbidden.filter(token => svg.includes(token));
if (missing.length || forbiddenHits.length) {{
  console.log(JSON.stringify({{missing, forbiddenHits}}, null, 2));
  process.exit(1);
}}
"""
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Output Grapher submove content-preservation check could not run: {exc}")
        return
    if result.returncode != 0:
        details = (result.stdout or result.stderr or "").strip()
        errors.append(f"Output Grapher submove content-preservation check failed: {details}")


def check_generated_burden_render_shape(errors: list[str]) -> None:
    fixture = r'''
daee-epistemics — NOETIC FIELD EXECUTION

Layer A — Compact DSL/IR Header
𝔅_LA (B_LA) = {¹B: baseline syntax}
𝔅_MRP (B_MRP) = {}
𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP
Initial burden set: [¹B]

Layer B — Governed Traversal

Burden ¹B — baseline syntax

¹B₁[FPD] — answer baseline syntax
Target: the baseline claim.
What it does: answers the visible baseline pressure without inventing a generated burden.
Result: the baseline pressure lands.
Contribution-to-Land(¹B): the baseline burden is landed.

The FPD operation tests the baseline claim as a visible premise rather than as an already-governed conclusion. It identifies the sentence-level pressure being carried by the reply, separates that pressure from any later rescue route, and blocks the reply from importing a broader framework before the local syntax has first been answered. The state change is narrow but real: the baseline burden is discharged by owner-backed operation, not by the mere presence of Target/Operation/Result labels.

Land(¹B): landed.

[Mid-Reread Pressure]
Target: ¹B
Route-gradient:
Finding: genuine-dependent
MRP route result type: generated_burden_instantiation
MRP resultant: non-baseline recoil remains live.
Graph delta: ¹B → ²B
Field diagnostics: ∇·T: non-neutral / recoil remains; ∇×T: null
R(H,Δ): held routes rechecked: generated recoil; release/next: RECURSE to ²B

Burden ²B [generated-by: MRP(¹B)] — generated recoil
- generated-by: MRP(¹B)

²B₁[M8] — answer generated recoil
Target: the generated recoil.
What it does: traces the escape route exposed by the prior landing: the reply tries to treat an unworked held route as if it already rescued the baseline claim. M8 blocks that burden shift, separates the local claim from the broader framework, and requires the broader route to be reopened as a new burden rather than smuggled into closure.
Result: the generated recoil is barred from rescuing the baseline claim; it either becomes a worked B_MRP node or remains outside scoped closure.
Contribution-to-Land(²B): the state change discharges the generated burden by proving why Land(²B) follows from operation rather than code lookup or generated-by labels.

The M8 operation performs the generated-burden work rather than naming the desired conclusion. It identifies the hidden premise exposed by MRP: an unworked broader route is being treated as though it can retroactively repair a landed local premise. The operation distinguishes the original baseline claim from that new total-framework appeal, tests whether the broader route has been carried by any worked evidence in the current ledger, and blocks it from operating as a silent premise.

That produces a concrete graph state change. The recoil is no longer allowed to hover as informal immunity; it is either instantiated as a B_MRP burden with generated-by provenance or it remains non-load-bearing for the scoped claim. Because the generated pressure has now been made explicit, tested, and blocked from rescuing the baseline burden, Land(²B) follows from operation rather than from a summary label.

Land(²B): landed.

[Mid-Reread Pressure]
Target: ²B
Route-gradient:
Finding: stable
MRP route result type: no_new_resultant
MRP resultant: no new pressure remains.
Graph delta: none
Field diagnostics: ∇·T: neutral; ∇×T: resolved
R(H,Δ): all routes landed; release/next: STOP

Final Restorative Response
The response remains readable.

Closing Formulation
The closing remains visible.

Closure/Reconstruction Witness
Initial burden set: [¹B]
Terminal states:
¹B: landed
²B: landed
Burden dependency graph:
¹B (root) → ²B
MRP resultants:
MRP(¹B): type=generated_burden_instantiation; finding=genuine-dependent; graph=¹B → ²B; route=RECURSE
MRP(²B): type=no_new_resultant; finding=stable; graph=none; route=STOP

field_witness
{"B_LA":["B1"],"B_MRP":["B2"],"B_total":["B1","B2"],"nodes":["B1","B1_1","B2","B2_1"],"edges":[{"source":"B1","target":"B2","type":"generated_burden_instantiation"}],"generated_burdens":{"B2":{"generated_by":"MRP(B1)"}},"mrp_resultants":[{"source":"B1","type":"generated_burden_instantiation","route_gradient":"recoil remains","graph":"B1->B2","route":"RECURSE"},{"source":"B2","type":"no_new_resultant","route_gradient":"stable","graph":"none","route":"STOP"}],"reread_records":[{"source":"B1","R":"R(H,Delta)"}],"field_diagnostics":{"del_dot_T":"non-neutral then neutral","del_cross_T":"null then resolved"},"terminal_states":{"B1":{"state":"landed"},"B2":{"state":"landed"}},"closure":{"status":"COMPLETE"},"T_lang":"no guaranteed uptake","non_claims":["no hidden soul-state"],"coverage_proof":{"initial_burden_set":["B1"],"terminal_states":{"B1":{"state":"landed"},"B2":{"state":"landed"}},"dependency_graph":{"nodes":["B1","B2"],"edges":[{"from":"B1","to":"B2"}],"roots":["B1"],"parallel_groups":[],"acyclic":true}}}
'''
    parsed = parse_output(fixture)
    if parsed.generated_burdens.get("¹B"):
        errors.append("Python parser misclassified source burden ¹B as generated from a generated-by provenance line")
    if parsed.generated_burdens.get("²B") != "MRP(¹B)":
        errors.append("Python parser did not retain generated-by provenance for generated target ²B")
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
const source = {fixture!r};
eval(fs.readFileSync({str(JS)!r}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput(source, '');
const svg = window.daeeOutputGrapher.renderGraph(model);
const mainStart = svg.indexOf('Main problems in the reply');
const genStart = svg.indexOf('Preempted problems surfaced by reread');
const mainSegment = mainStart >= 0 && genStart > mainStart ? svg.slice(mainStart, genStart) : '';
const required = [
  'Main problems in the reply',
  'Preempted problems surfaced by reread',
  'Problem ²B',
  '[generated-by: MRP(¹B)]',
  'Result',
  'generated_burden_instantiation',
  'Ledger effect',
  'absent from B_LA',
  'Target:',
  'What it does:',
  'TTP operation body:',
  'Result:',
  'Contribution-to-Land:'
];
const missing = required.filter(token => !svg.includes(token));
const errors = [];
if (!mainSegment) errors.push('could not isolate Main problems segment');
if (mainSegment.includes('Problem ²B')) errors.push('generated B_MRP was backfilled into Main problems section');
if (model.generatedBurdens['¹B']) errors.push('source burden ¹B was misclassified as generated from a generated-by provenance line');
if (model.generatedBurdens['²B'] !== 'MRP(¹B)') errors.push('generated target ²B did not retain generated-by provenance');
const generatedBody = model.bodyExtract?.submoveDetails?.['²B₁']?.body || '';
if (!generatedBody.includes('That produces a concrete graph state change')) errors.push('Contribution-to-Land Land(...) text truncated the generated submove operation body');
if (model.errors.length) errors.push('parser errors: ' + model.errors.join('; '));
if (missing.length) errors.push('missing render tokens: ' + missing.join(', '));
if (errors.length) {{
  console.log(JSON.stringify({{errors, mainSegment: mainSegment.slice(0, 600)}}, null, 2));
  process.exit(1);
}}
"""
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Output Grapher generated-burden render-shape check could not run: {exc}")
        return
    if result.returncode != 0:
        details = (result.stdout or result.stderr or "").strip()
        errors.append(f"Output Grapher generated-burden render-shape check failed: {details}")


def check_restoration_summary_count_consistency(errors: list[str]) -> None:
    fixture = r'''
daee-epistemics — NOETIC FIELD EXECUTION

Layer A — Compact DSL/IR Header
𝔅_LA (B_LA) = {¹B grammar, ²B analogy, ³B antecedent, ⁴B predication}
𝔅_MRP (B_MRP) = {}
𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP
Initial burden set: [¹B, ²B, ³B, ⁴B]

Layer B — Governed Traversal

Burden ¹B — grammar
¹B₁[FPD] — answer grammar
Target: grammar.
What it does: answers grammar.
Result: grammar landed.
Contribution-to-Land(¹B): grammar lands.
Land(¹B): landed.
[Mid-Reread Pressure]
Target: ¹B
R(H,Δ): held routes rechecked: ²B; live remainder: analogy; release/next: ²B held_burden_activation
MRP route result type: held_burden_activation
MRP resultant: ¹B -> ²B
Graph delta: ¹B → ²B
Route: RECURSE

Burden ²B — analogy
²B₁[FPD] — answer analogy
Target: analogy.
What it does: answers analogy.
Result: analogy landed.
Contribution-to-Land(²B): analogy lands.
Land(²B): landed.
[Mid-Reread Pressure]
Target: ²B
R(H,Δ): held routes rechecked: ³B; live remainder: antecedent; release/next: ³B held_burden_activation
MRP route result type: held_burden_activation
MRP resultant: ²B -> ³B
Graph delta: ²B → ³B
Route: RECURSE

Burden ³B — antecedent
³B₁[FPD] — answer antecedent
Target: antecedent.
What it does: answers antecedent.
Result: antecedent landed.
Contribution-to-Land(³B): antecedent lands.
Land(³B): landed.
[Mid-Reread Pressure]
Target: ³B
R(H,Δ): held routes rechecked: ⁴B; live remainder: predication; release/next: ⁴B held_burden_activation
MRP route result type: held_burden_activation
MRP resultant: ³B -> ⁴B
Graph delta: ³B → ⁴B
Route: RECURSE

Burden ⁴B — predication
⁴B₁[FPD] — answer predication
Target: predication.
What it does: answers predication.
Result: predication landed.
Contribution-to-Land(⁴B): predication lands.
Land(⁴B): landed.
[Mid-Reread Pressure]
Target: ⁴B
R(H,Δ): held routes rechecked: generated recoil; live remainder: ⁵B absent from B_LA; release/next: generated_burden_instantiation
MRP route result type: generated_burden_instantiation
MRP resultant: instantiate ⁵B [generated-by: MRP(⁴B)]
Graph delta: ⁴B → ⁵B
Route: RECURSE

Burden ⁵B [generated-by: MRP(⁴B)] — generated recoil
⁵B₁[FPD] — answer recoil
Target: generated recoil.
What it does: exposes the hidden premise that a broader unargued framework can retroactively rescue the local claim. It distinguishes the original local argument from the new total-system appeal, requires that new appeal to be stated as its own burden, and blocks it from being smuggled into closure as if it had already been tested.
Result: the generated recoil is separated from the baseline claim and cannot rescue it without becoming a new worked burden.
Contribution-to-Land(⁵B): the state change lands the generated burden by showing why the recoil is non-load-bearing for the scoped closure.

The FPD operation identifies the hidden premise created by the post-land recoil: once the local proof has failed, unworked broader material is being used as if it can retroactively repair the defeated claim. That is a scope shift from the offered argument to an unstated total-system reserve. The operation distinguishes the original baseline burdens from this new immunity appeal, makes the hidden premise explicit, and tests whether it has actually been carried by any evidence in the current burden ledger.

Because that premise has not been worked, the broader material cannot function as hidden support for the local claim. The state delta is specific: the recoil is classified as generated B_MRP, barred from backfilling B_LA, and either worked here or held as a distinct future burden. In this fixture it is worked and shown non-load-bearing for the scoped closure, so Land(⁵B) follows from the owner operation rather than from the conclusion word "recoil."
Land(⁵B): landed.
[Mid-Reread Pressure]
Target: ⁵B
R(H,Δ): held routes rechecked: none load-bearing; live remainder: none; release/next: STOP
MRP route result type: no_new_resultant
MRP resultant: stable.
Graph delta: none
Route: STOP

Restorative Response
Response.

Closing Formulation
Closing.

Closure/Reconstruction Witness
Initial burden set: [¹B, ²B, ³B, ⁴B]
𝔅_LA (B_LA) = {¹B, ²B, ³B, ⁴B}
𝔅_MRP (B_MRP) = {⁵B}
𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP
Terminal states:
¹B: landed
²B: landed
³B: landed
⁴B: landed
⁵B: landed
Burden dependency graph: ¹B → ²B → ³B → ⁴B → ⁵B
MRP resultants:
MRP(¹B): type=held_burden_activation; graph=¹B → ²B; route=RECURSE
MRP(²B): type=held_burden_activation; graph=²B → ³B; route=RECURSE
MRP(³B): type=held_burden_activation; graph=³B → ⁴B; route=RECURSE
MRP(⁴B): type=generated_burden_instantiation; graph=⁴B → ⁵B; route=RECURSE
MRP(⁵B): type=no_new_resultant; graph=none; route=STOP

field_witness
{"B_LA":["B1","B2","B3","B4"],"B_MRP":["B5"],"B_total":["B1","B2","B3","B4","B5"],"nodes":["B1","B2","B3","B4","B5"],"edges":[{"source":"B1","target":"B2","type":"held_burden_activation"},{"source":"B2","target":"B3","type":"held_burden_activation"},{"source":"B3","target":"B4","type":"held_burden_activation"},{"source":"B4","target":"B5","type":"generated_burden_instantiation"}],"generated_burdens":{"B5":{"generated_by":"MRP(B4)"}},"mrp_resultants":[{"source":"B1","type":"held_burden_activation","graph":"B1->B2","route":"RECURSE"},{"source":"B2","type":"held_burden_activation","graph":"B2->B3","route":"RECURSE"},{"source":"B3","type":"held_burden_activation","graph":"B3->B4","route":"RECURSE"},{"source":"B4","type":"generated_burden_instantiation","graph":"B4->B5","route":"RECURSE"},{"source":"B5","type":"no_new_resultant","graph":"none","route":"STOP"}],"terminal_states":{"B1":{"state":"landed"},"B2":{"state":"landed"},"B3":{"state":"landed"},"B4":{"state":"landed"},"B5":{"state":"landed"}},"closure":{"status":"COMPLETE"}}
'''
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
const source = {fixture!r};
eval(fs.readFileSync({str(JS)!r}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput(source, '');
const svg = window.daeeOutputGrapher.renderGraph(model);
const accountedCount = (svg.match(/Accounted for:/g) || []).length;
const errors = [];
if (!svg.includes('The rebuttal accounted for 5/5 problems.')) errors.push('missing 5/5 visible summary count');
if (accountedCount !== 5) errors.push(`Restoration Summary count mismatch: summary reports 5/5 accounted burdens, but only ${{accountedCount}} accounted burden items are rendered.`);
if (!svg.includes('Accounted for: Problem ⁵B')) errors.push('generated B_MRP was not included in the accounted list');
if (!svg.includes('[generated-by: MRP(⁴B)]')) errors.push('generated burden provenance missing from accounted list or graph');
if (model.errors.length) errors.push('parser errors: ' + model.errors.join('; '));
if (errors.length) {{
  console.log(JSON.stringify({{errors, accountedCount}}, null, 2));
  process.exit(1);
}}
"""
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Output Grapher restoration-summary count check could not run: {exc}")
        return
    if result.returncode != 0:
        details = (result.stdout or result.stderr or "").strip()
        errors.append(f"Output Grapher restoration-summary count check failed: {details}")


def check_source_section_preservation(errors: list[str]) -> None:
    fixture = r'''
╔════════════════════════════════════════════╗
║ daee-epistemics — NOETIC FIELD EXECUTION ║
╚════════════════════════════════════════════╝

**Layer A — Compact DSL/IR Header**
- read status: source sections must survive the map
- held: B1, B2

### Burden 1 — Imported moral tribunal
**Hidden premises operating in the statement:**
- hidden premise one
- hidden premise two

¹B₁ [FPD] — expose the imported tribunal
Target: the hidden court imported by the reply.
What it does: names the court before it judges the noetic field.
Result: the hidden premise is no longer invisible.
Contribution-to-Land(¹B): the first burden lands from visible body prose.

**Land(¹B):** the imported tribunal loses authority.

**[Mid-Reread Pressure]**
Target: ¹B
Pressure activations: ²B remains live
∇·T: non-neutral toward the next burden
∇×T: null
Finding: known issue still had to be answered
Graph delta: ¹B → ²B
Route: RECURSE
Boundary: T_lang respected
MRP resultant: held_burden_activation

### Burden 2 — Accountability compression
**Layer A — Burden 2**
- local setup one
- local setup two

²B₁ [M1] — expose compression
Target: the compressed accountability claim.
What it does: restores the missing distinction.
Result: the compression no longer carries the argument.
Contribution-to-Land(²B): the second burden lands from source text.

**Land(²B):** the compression is discharged.

**[Mid-Reread Pressure]**
Target: ²B
Pressure activations: none
∇·T: neutral
∇×T: null
Finding: no new pressure remains
Graph delta: none
Route: STOP
Boundary: T_lang respected
MRP resultant: no_new_resultant

## Closure/Reconstruction Witness
coverage_complete=true
terminal states: ¹B=landed; ²B=landed

## Final Restorative Response — For the Dāʿī

The visible final restorative response must appear after the restoration summary and before the formal appendix.

## Final Closing Formulation

The closing formulation must remain visible and cannot be replaced by the formal case fill.
'''
    required_fragments = [
        "What structure was detected",
        "Layer A / Compact DSL-IR detected",
        "Hidden premises operating in the statement",
        "Problem setup from the output",
        "Follow-up: pressure-check",
        "Restorative Response",
        "The visible final restorative response must appear",
        "Closing Formulation",
        "The closing formulation must remain visible",
    ]
    model_required = [
        ["compact_layer_a", "banner", "hidden_premises", "burden_setup", "mid_reread_pressure", "closure_witness", "restorative_response", "closing_formulation"],
        ["¹B", "²B"],
    ]
    node_script = f"""
const fs = require('fs');
global.window = {{}};
global.document = {{
  addEventListener: () => {{}},
  getElementById: () => null,
  querySelectorAll: () => []
}};
const source = {fixture!r};
eval(fs.readFileSync({str(JS)!r}, 'utf8'));
const model = window.daeeOutputGrapher.parseOutput(source, '');
const svg = window.daeeOutputGrapher.renderGraph(model);
const required = {required_fragments!r};
const missing = required.filter(token => !svg.includes(token));
const forbiddenPublic = [
  'Source structure detected in the output',
  'Layer A — Compact DSL/IR Header',
  'Layer A — Compact Diagnostic Surface',
  'Source block: [Mid-Reread Pressure]',
  'Closure/Reconstruction Witness',
  'Closure / Reconstruction Witness',
  'Formal Case Fill',
  'MRP resultants',
  '∇·B:',
  '∇×κ:',
  '𝒞(Ψᴺ):',
  '```',
  '**',
  '*'
];
const formalStart = svg.indexOf('outputGrapherFormalSection');
const publicLeaks = forbiddenPublic.filter(token => {{
  let index = svg.indexOf(token);
  while (index >= 0) {{
    if (formalStart < 0 || index < formalStart) return true;
    index = svg.indexOf(token, index + token.length);
  }}
  return false;
}});
const requiredTypes = {model_required[0]!r};
const types = new Set((model.sourceSections || []).map(section => section.type));
const missingTypes = requiredTypes.filter(type => !types.has(type));
const requiredBurdens = {model_required[1]!r};
const setupMissing = requiredBurdens.filter(b => !(model.bodyExtract.mrpSourceTexts || {{}})[b]);
if (!model.restorativeResponse || !model.closingFormulation) missing.push('final prose model fields');
if (svg.includes('Plain-language Rebuttal View')) missing.push('old plain-language label absent');
const coverage = (model.sourceSections || []).map(section => ({{
  type: section.type,
  assignedRenderSection: section.assignedRenderSection,
  renderLayer: window.daeeOutputGrapher.sourceRenderLayer ? window.daeeOutputGrapher.sourceRenderLayer(section.type) : null
}}));
if (missing.length || missingTypes.length || setupMissing.length || publicLeaks.length) {{
  console.log(JSON.stringify({{missing, missingTypes, setupMissing, publicLeaks, sourceSections:model.sourceSections, coverage}}, null, 2));
  process.exit(1);
}}
"""
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Output Grapher source-section preservation check could not run: {exc}")
        return
    if result.returncode != 0:
        details = (result.stdout or result.stderr or "").strip()
        errors.append(f"Output Grapher source-section preservation check failed: {details}")


def check_fixtures(errors: list[str]) -> None:
    if not FIXTURE_ROOT.exists():
        errors.append(f"{rel(FIXTURE_ROOT)} is missing")
        return
    fixtures = sorted(FIXTURE_ROOT.glob("*.md"))
    if not fixtures:
        errors.append(f"{rel(FIXTURE_ROOT)} has no fixtures")
        return
    seen = {path.name for path in fixtures}
    required = {
        "valid-simple-closure.md",
        "valid-mrp-held-burden-activation.md",
        "valid-mrp-generated-burden.md",
        "valid-hard-compound-reconstructible.md",
        "valid-restorative-response-closing-formulation.md",
        "invalid-missing-terminal-state.md",
        "invalid-stop-before-continuation.md",
        "invalid-edge-missing-mrp-resultant.md",
        "invalid-coverage-complete-with-live-divergence.md",
        "invalid-legacy-notation-warning.md",
        "invalid-field-witness-omits-generated-b-mrp.md",
        "invalid-field-witness-baseline-marked-generated.md",
        "invalid-field-witness-ledger-disagreement.md",
        "invalid-field-witness-unresolved-held-route-closure.md",
    }
    missing = sorted(required - seen)
    if missing:
        errors.append(f"{rel(FIXTURE_ROOT)} missing fixtures: {missing}")
    for path in fixtures:
        text = path.read_text(encoding="utf-8")
        witness_path = path.with_suffix(".field_witness.json")
        field_witness = witness_path.read_text(encoding="utf-8") if witness_path.exists() else None
        result = parse_output(text, field_witness)
        mode = expected_mode(text, path)
        has_embedded_witness = bool(extract_embedded_field_witness(text))
        no_graph_mode = bool(
            re.search(
                r"(?is)\b(?:minimal|short|no-graph)\b.{0,120}\bgraph(?:ing)?\s+(?:unsupported|partial)|"
                r"\bgraph(?:ing)?\s+(?:unsupported|partial)\b.{0,120}\b(?:minimal|short|no-graph)\b",
                text,
            )
        )
        if mode == "pass" and not (field_witness or has_embedded_witness or no_graph_mode):
            errors.append(f"{rel(path)} expected pass but lacks field_witness / graphable reconstruction payload")
        if mode == "pass" and result.errors:
            errors.append(f"{rel(path)} expected pass but failed: {result.errors}")
        elif mode == "fail" and not result.errors:
            errors.append(f"{rel(path)} expected hard failure but passed")
        elif mode == "warn":
            if result.errors:
                errors.append(f"{rel(path)} expected warning-only but failed: {result.errors}")
            if not result.warnings:
                errors.append(f"{rel(path)} expected warnings but emitted none")
        if path.name == "valid-mrp-generated-burden.md":
            if "²B" not in result.generated_burdens:
                errors.append(f"{rel(path)} did not mark ²B as generated by MRP")
            if not result.submoves.get("²B"):
                errors.append(f"{rel(path)} generated burden lacks submoves")
        if mode == "pass":
            rendered = graph_html(result, path.name)
            if "<svg" not in rendered or "<rect" not in rendered or "<line" not in rendered:
                errors.append(f"{rel(path)} did not render an exportable SVG/HTML graph structure")
        if path.name == "invalid-reconstructible-with-public-alias-warning.md":
            if result.errors:
                errors.append(f"{rel(path)} should be graph-reconstructible while warning-only: {result.errors}")
            if not result.warnings:
                errors.append(f"{rel(path)} should emit a public alias warning")
            if not warning_failures(result.warnings):
                errors.append(f"{rel(path)} must be rejected by proof-mode warning gate")


def check_skill_output(
    path: Path,
    expect_reconstructible: bool,
    allow_nonreconstructible: bool,
    fail_on_warnings: bool,
    out: Path | None,
) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    result = parse_output(text)
    js_result = parse_skill_output_with_browser_js(path)
    for item in js_result["errors"]:
        result.errors.append(f"browser Output Grapher parser: {item}")
    if not extract_embedded_field_witness(text) and not re.search(
        r"(?is)\b(?:minimal|short|no-graph)\b.{0,120}\bgraph(?:ing)?\s+(?:unsupported|partial)|"
        r"\bgraph(?:ing)?\s+(?:unsupported|partial)\b.{0,120}\b(?:minimal|short|no-graph)\b",
        text,
    ):
        result.errors.append("normal governed output lacks field_witness / graphable reconstruction payload")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(graph_html(result, f"Output Grapher Smoke: {path.name}"), encoding="utf-8")
    summary = result_summary(result)
    print(f"skill-output: {path}")
    print(f"- reconstructible: {summary['reconstructible']}")
    print(f"- burdens: {len(summary['burdens'])}")
    print(f"- submoves: {summary['submove_count']}")
    print(f"- MRP resultants: {summary['mrp_count']}")
    print(f"- terminals: {summary['terminal_count']}")
    if out:
        print(f"- graph artifact: {out}")
    for item in summary["errors"]:
        print(f"ERROR: {item}")
    for item in summary["warnings"]:
        print(f"WARN: {item}")
    if fail_on_warnings and result.warnings:
        for item in warning_failures(result.warnings):
            print(f"ERROR: {item}")
        return 1
    if result.errors and not allow_nonreconstructible:
        return 1
    if expect_reconstructible and result.errors:
        return 1
    return 0


def output_artifact_path(out: Path | None, skill_outputs: list[Path], path: Path) -> Path | None:
    if not out:
        return None
    if len(skill_outputs) == 1:
        return out
    return out / f"{path.stem}.html"


def check_skill_outputs(
    paths: list[Path],
    expect_reconstructible: bool,
    allow_nonreconstructible: bool,
    fail_on_warnings: bool,
    out: Path | None,
) -> int:
    failures = 0
    if out and len(paths) > 1:
        out.mkdir(parents=True, exist_ok=True)
        print(f"skill-output batch graph directory: {out}")
    for path in paths:
        artifact = output_artifact_path(out, paths, path)
        status = check_skill_output(path, expect_reconstructible, allow_nonreconstructible, fail_on_warnings, artifact)
        if status:
            failures += 1
    if len(paths) > 1:
        print(f"skill outputs checked: {len(paths)}")
        print(f"skill output failures: {failures}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-output", type=Path, nargs="+", help="Parse one or more real/local skill outputs")
    parser.add_argument("--expect-reconstructible", action="store_true")
    parser.add_argument(
        "--allow-nonreconstructible",
        action="store_true",
        help="Diagnostics-only mode for legacy/broken outputs; without this, --skill-output fails on parse errors.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat parser warnings as failures for release/current proof gates.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help=(
            "Write an HTML graph artifact for --skill-output. With multiple outputs, "
            "this is treated as an output directory."
        ),
    )
    args = parser.parse_args(argv)

    if args.skill_output:
        return check_skill_outputs(
            args.skill_output,
            args.expect_reconstructible,
            args.allow_nonreconstructible,
            args.fail_on_warnings,
            args.out,
        )

    errors: list[str] = []
    check_static_artifact(errors)
    check_fixtures(errors)
    if errors:
        print("output grapher check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("output grapher check: PASS")
    print(f"- fixtures: {len(list(FIXTURE_ROOT.glob('*.md')))}")
    print(f"- artifact: {rel(SECTION)}")
    print(f"- parser: {rel(JS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
