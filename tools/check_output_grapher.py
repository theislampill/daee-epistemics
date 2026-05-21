#!/usr/bin/env python3
"""Validate the docs Output Collapse Grapher artifact and fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

from output_grapher_lib import burden_token, graph_html, parse_output, result_summary

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
        "section ZIP button label": "Export sections as PNG ZIP",
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
        "case headline for Trinitarian smoke": "CASE: Trinitarian reply to John 17:3",
        "restoration bullet builder": "restorationBullets",
        "formal case fill": "Formal Case Fill",
        "formal case fill renderer": "renderFormalCaseFill",
        "story view renderer": "renderStorySvg",
        "story burden cards": "outputGrapherStoryBurden",
        "plain claim label": "Reply / claim being rejected",
        "plain conclusion label": "Final Answer From The Output",
        "plain dependency label": "What the reply depends on",
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
        "source MRP block renderer": "outputGrapherMrpSourceBlock",
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
    if "Target', details.target" not in js_text or "Result', details.result" not in js_text or "Contribution', details.contribution" not in js_text:
        errors.append("Output Grapher submove cards must render body-derived target/result/contribution details")
    if "labelSize" not in js_text or "bodySize" not in js_text or "font-weight" not in js_text:
        errors.append("Output Grapher submove cards must use differentiated label/body typography")
    if "['Graph movement', graph]" not in js_text or "['Route', route]" not in js_text:
        errors.append("Output Grapher MRP panel must render structured graph movement and route rows")
    if "cloneSvgForExport(svg)" not in js_text or "viewBox',`${-padding}" not in js_text:
        errors.append("Output Grapher exports must use a padded full-viewBox SVG clone")
    if "Main Problems In The Reply" in combined and "bodyBurdenDescription(model,b)" not in js_text:
        errors.append("Output Grapher burden inventory must use visible body headings, not witness-only labels")
    check_submove_content_preservation(js_text, errors)
    check_source_section_preservation(errors)
    check_single_paste_embedded_witness(errors)


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
{"nodes":["B1"],"edges":[]}
"""
    result = parse_output(source)
    if result.errors:
        errors.append(f"single pasted output with embedded field_witness should parse without errors: {result.errors}")
    disagreed = parse_output(source, '{"nodes":["B2"],"edges":[]}')
    if not any("embedded field_witness and separate field_witness disagree" in warning for warning in disagreed.visible_vs_field_witness):
        errors.append("separate field_witness JSON must be compared against embedded field_witness and warn on disagreement")
    if burden_token(1) not in disagreed.body_burdens:
        errors.append("visible body burden set must remain separate from field_witness structural nodes")
    if burden_token(2) in disagreed.body_burdens:
        errors.append("visible body burden set must stop before closure witness / field_witness structural nodes")
    edge_disagreed = parse_output(source, '{"nodes":["B1"],"edges":[["B1","B1"]]}')
    if not any("edge mismatch visible=" in warning for warning in edge_disagreed.visible_vs_field_witness):
        errors.append("field_witness edge mismatches must be reported, not only node mismatches")


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
        "Contribution:",
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
        "Source structure detected in the output",
        "Layer A — Compact DSL/IR Header",
        "Hidden premises operating in the statement",
        "Layer A — Burden 2",
        "Source block: [Mid-Reread Pressure]",
        "Pressure activations",
        "MRP resultant",
        "Restorative Response",
        "The visible final restorative response must appear",
        "Closing Formulation",
        "The closing formulation must remain visible",
        "Closure/Reconstruction Witness",
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
const requiredTypes = {model_required[0]!r};
const types = new Set((model.sourceSections || []).map(section => section.type));
const missingTypes = requiredTypes.filter(type => !types.has(type));
const requiredBurdens = {model_required[1]!r};
const setupMissing = requiredBurdens.filter(b => !(model.bodyExtract.mrpSourceTexts || {{}})[b]);
if (!model.restorativeResponse || !model.closingFormulation) missing.push('final prose model fields');
if (svg.includes('Plain-language Rebuttal View')) missing.push('old plain-language label absent');
if (missing.length || missingTypes.length || setupMissing.length) {{
  console.log(JSON.stringify({{missing, missingTypes, setupMissing, sourceSections:model.sourceSections}}, null, 2));
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


def check_skill_output(path: Path, expect_reconstructible: bool, out: Path | None) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    result = parse_output(text)
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
    if expect_reconstructible and result.errors:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-output", type=Path, help="Parse a real/local skill output")
    parser.add_argument("--expect-reconstructible", action="store_true")
    parser.add_argument("--out", type=Path, help="Write an HTML graph artifact for --skill-output")
    args = parser.parse_args(argv)

    if args.skill_output:
        return check_skill_output(args.skill_output, args.expect_reconstructible, args.out)

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
