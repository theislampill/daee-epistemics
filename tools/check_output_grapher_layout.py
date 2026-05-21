#!/usr/bin/env python3
"""Guard the Output Grapher story-view layout against clipped infographic cards."""

from __future__ import annotations

from pathlib import Path
import re
import json
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "index" / "output-grapher.js"
CSS = ROOT / "docs" / "index" / "output-grapher.css"
SECTION = ROOT / "docs" / "index" / "sections" / "output-grapher.html"
SMOKE_G2 = ROOT / ".daee" / "output-grapher-smokes" / "fresh" / "G2-trinitarian-reply.md"
RENDERED_METRICS = ROOT / ".daee" / "output-grapher-graphs" / "fresh" / "G2-rendered-layout-metrics.json"
NODE_MODULES = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules" / ".pnpm" / "node_modules"
TERMINAL_BOTTOM_PADDING_MIN = 0
TERMINAL_BOTTOM_PADDING_MAX = 30
GLOBAL_BOTTOM_PADDING_MIN = 24
GLOBAL_BOTTOM_PADDING_MAX = 80
POST_TERMINAL_BOTTOM_PADDING_MAX = 140
EXPORTED_BOTTOM_PADDING_MIN = 64
EXPORTED_BOTTOM_PADDING_MAX = 140


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def render_story_body(js_text: str) -> str:
    match = re.search(r"function renderStorySvg\(model(?:,[^)]*)?\)\{(?P<body>.*?)\n  function renderGraph\(model\)\{", js_text, re.S)
    return match.group("body") if match else ""


def rendered_layout_check(errors: list[str]) -> None:
    if not SMOKE_G2.exists():
        return
    RENDERED_METRICS.parent.mkdir(parents=True, exist_ok=True)
    node_script = f"""
const fs = require('fs');
const path = require('path');
const {{ chromium }} = require('playwright-core');
const root = {str(ROOT).replace(chr(92), '/').__repr__()};
const js = fs.readFileSync(path.join(root,'docs/index/output-grapher.js'),'utf8');
const smoke = fs.readFileSync({str(SMOKE_G2).replace(chr(92), '/').__repr__()},'utf8');
const safeJs = js.split('</script').join('<\\\\/script');
const safeSmoke = JSON.stringify(smoke).split('</script').join('<\\\\/script');
const html = `<!doctype html><meta charset="utf-8"><style>body{{margin:0;background:#050914;color:white;font-family:Segoe UI,Arial,sans-serif}}.wrap{{width:1800px;margin:0 auto}}</style><div class="wrap" id="graph"></div><script>${{safeJs}}</script><script>const model=window.daeeOutputGrapher.parseOutput(${{safeSmoke}},'');document.getElementById('graph').innerHTML=window.daeeOutputGrapher.renderGraph(model);</script>`;
(async () => {{
  const browser = await chromium.launch({{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true}});
  const page = await browser.newPage({{viewport:{{width:1900,height:2600}}, deviceScaleFactor:1}});
  await page.setContent(html,{{waitUntil:'load'}});
  await page.waitForTimeout(200);
    const metrics = await page.evaluate(() => {{
    const svg = document.querySelector('svg');
    function panelBottomPadding(selector, limit=30) {{
      return [...svg.querySelectorAll(selector)].slice(0, limit).map(g => {{
        const rect = g.querySelector('rect');
        if (!rect) return null;
        const rb = rect.getBBox();
        let contentBottom = rb.y;
        for (const el of g.querySelectorAll('text,circle,line')) {{
          const b = el.getBBox();
          contentBottom = Math.max(contentBottom, b.y + b.height);
        }}
        return {{
          className: g.getAttribute('class') || '',
          height: rb.height,
          bottomPadding: (rb.y + rb.height) - contentBottom,
          text: g.textContent.replace(/\\s+/g,' ').trim().slice(0,120)
        }};
      }}).filter(Boolean);
    }}
    function terminalBottomPadding() {{
      return panelBottomPadding('.outputGrapherRestorationSummary, .outputGrapherRestorativeResponse, .outputGrapherClosingFormulation, .outputGrapherFormalCaseFill', 20);
    }}
    function elementBox(selector) {{
      const el = svg.querySelector(selector);
      if (!el) return null;
      const b = el.getBoundingClientRect();
      const sb = svg.getBoundingClientRect();
      return {{
        top: b.top - sb.top,
        bottom: b.bottom - sb.top,
        height: b.height,
        text: el.textContent.replace(/\\s+/g,' ').trim().slice(0,120)
      }};
    }}
    const routeRows = [...svg.querySelectorAll('.outputGrapherRouteRow')].map(g => {{
      const rect = g.querySelector('rect');
      const rb = rect.getBBox();
      let maxText = 0;
      for (const t of g.querySelectorAll('text')) maxText = Math.max(maxText, t.getBBox().width);
      return {{
        width: rb.width,
        innerTextWidth: Number(g.getAttribute('data-inner-text-width') || 0),
        routeBadgeWidth: Number(g.getAttribute('data-route-badge-width') || 0),
        maxText,
        text: g.textContent.replace(/\\s+/g,' ').trim()
      }};
    }});
    const submoves = [...svg.querySelectorAll('.outputGrapherStorySubmove')].slice(0,8).map(g => {{
      const rect = g.querySelector('rect');
      const rb = rect.getBBox();
      let maxText = 0;
      for (const t of g.querySelectorAll('text')) maxText = Math.max(maxText, t.getBBox().width);
      return {{
        width: rb.width,
        innerTextWidth: Number(g.getAttribute('data-inner-text-width') || 0),
        maxText,
        usageRatio: maxText / Number(g.getAttribute('data-inner-text-width') || rb.width)
      }};
    }});
    const coverage = window.daeeOutputGrapher.exportCoverageReport();
    const sectionPlan = window.daeeOutputGrapher.sectionExportPlan();
    const restorationText = svg.querySelector('.outputGrapherRestorationSummary')?.textContent || '';
    return {{
      viewBox: svg.getAttribute('viewBox'),
      headerStatusBadges: [...svg.querySelectorAll('.outputGrapherStoryBurden > text')].filter(t => /^(Landed|RECURSE|STOP|Held)$/i.test(t.textContent.trim())).length,
      rawHeaderBadgeText: />Landed<|>RECURSE<|>STOP</.test(svg.outerHTML),
      inFlowGuideText: /How to read this map/i.test(svg.textContent),
      routeRowCount: routeRows.length,
      largeRouteCards: svg.querySelectorAll('.outputGrapherRoutePanel').length,
      restorationSummaryCount: svg.querySelectorAll('.outputGrapherRestorationSummary').length,
      restorativeResponseCount: svg.querySelectorAll('.outputGrapherRestorativeResponse').length,
      closingFormulationCount: svg.querySelectorAll('.outputGrapherClosingFormulation').length,
      formalCaseFillCount: svg.querySelectorAll('.outputGrapherFormalCaseFill').length,
      publicInsiderLeaks: [
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
      ].filter(token => svg.textContent.includes(token) || svg.outerHTML.includes(token)),
      restorationContainsTechnicalProofStrip: restorationText.includes('Technical proof strip'),
      restorationContainsTechnicalAppendix: /Technical proof|Formal Reconstruction|Formal Case Fill|Technical appendix/i.test(restorationText),
      duplicateLandTechnicalLines: [...svg.querySelectorAll('.outputGrapherStoryPanel')].filter(g => /Technical:\\s*Land\\(/.test(g.textContent)).length,
      duplicateRereadTechnicalLines: [...svg.querySelectorAll('.outputGrapherStoryPanel')].filter(g => /Technical:\\s*R\\(H,/.test(g.textContent)).length,
      legendCount: svg.querySelectorAll('.ogSvgLegend').length,
      exportCoverage: coverage,
      sectionPlan,
      finalSectionOrder: {{
        restorationSummary: elementBox('.outputGrapherRestorationSummary'),
        restorativeResponse: elementBox('.outputGrapherRestorativeResponse'),
        closingFormulation: elementBox('.outputGrapherClosingFormulation'),
        formalCaseFill: elementBox('.outputGrapherFormalCaseFill'),
        legend: elementBox('.ogSvgLegend')
      }},
      globalBottomPadding: {{
        postTerminalCard: coverage?.postTerminalCardBottomPadding,
        postLegend: coverage?.postLegendBottomPadding,
        exported: coverage?.exportedBottomPadding,
        legendGapAfterTerminal: coverage?.legendGapAfterTerminal
      }},
      routeRows,
      submoves,
      bottomPaddingPanels: panelBottomPadding('.outputGrapherStoryPanel, .outputGrapherStorySubmove, .outputGrapherRouteRow, .outputGrapherKeyValuePanel, .outputGrapherRestorationSummary, .outputGrapherFinalBodyProse'),
      terminalBottomPadding: terminalBottomPadding()
    }};
  }});
  await browser.close();
  fs.writeFileSync({str(RENDERED_METRICS).replace(chr(92), '/').__repr__()}, JSON.stringify(metrics,null,2));
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
    env = os.environ.copy()
    env["NODE_PATH"] = str(NODE_MODULES)
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"rendered Output Grapher layout check could not run: {exc}")
        return
    if result.returncode != 0:
        errors.append(f"rendered Output Grapher layout check failed: {(result.stderr or result.stdout).strip()}")
        return
    metrics = json.loads(RENDERED_METRICS.read_text(encoding="utf-8"))
    if metrics.get("headerStatusBadges"):
        errors.append("rendered story view still has repeated burden-header status badges")
    if metrics.get("largeRouteCards"):
        errors.append("rendered story view still uses large route panel cards instead of compact route rows")
    if metrics.get("inFlowGuideText"):
        errors.append("rendered story view still inserts a large How-to-read guide inside the map flow")
    if metrics.get("restorationContainsTechnicalAppendix"):
        errors.append("rendered Restoration Summary still contains technical appendix/proof content")
    elif metrics.get("restorationContainsTechnicalProofStrip"):
        errors.append("rendered Restoration Summary still contains the insider technical proof strip")
    if metrics.get("duplicateLandTechnicalLines") or metrics.get("duplicateRereadTechnicalLines"):
        errors.append("rendered Land/Reread panels still duplicate their corner badges with Technical lines")
    if metrics.get("publicInsiderLeaks"):
        errors.append(f"default Restorative Noetic Map leaks insider/raw source text: {metrics.get('publicInsiderLeaks')}")
    if metrics.get("routeRowCount", 0) < 1:
        errors.append("rendered story view did not render compact route rows")
    order = metrics.get("finalSectionOrder") or {}
    ordered_keys = ["restorationSummary", "restorativeResponse", "closingFormulation", "legend"]
    if all(isinstance(order.get(key), dict) for key in ordered_keys):
        tops = {key: float(order[key].get("top") or 0) for key in ordered_keys}
        if not (
            tops["restorationSummary"]
            < tops["restorativeResponse"]
            < tops["closingFormulation"]
            < tops["legend"]
        ):
            errors.append(
                "rendered final section order is wrong: expected Restoration Summary -> "
                "Restorative Response -> Closing Formulation -> Legend"
            )
    if isinstance(order.get("formalCaseFill"), dict):
        errors.append("default Restorative Noetic Map should not render Formal Case Fill in the public flow")
    coverage = metrics.get("exportCoverage") or {}
    if not coverage.get("hasRestorationSummary"):
        errors.append("export coverage report is missing the Restoration Summary")
    if not coverage.get("hasRestorativeResponse"):
        errors.append("export coverage report is missing the Restorative Response")
    if not coverage.get("hasClosingFormulation"):
        errors.append("export coverage report is missing the Closing Formulation")
    if not coverage.get("hasFormalCaseFill"):
        errors.append("export coverage report is missing the Formal Case Fill appendix")
    if not coverage.get("hasLegend"):
        errors.append("export coverage report is missing the legend")
    if not coverage.get("hasFinalBurden"):
        errors.append("export coverage report is missing the final burden card")
    if coverage.get("sectionedExportType") != "zip":
        errors.append("section export must be a PNG ZIP, not loose PNG downloads")
    if not coverage.get("hasSectionManifest"):
        errors.append("section export coverage must report a manifest.json")
    expected_section_count = int(coverage.get("burdenCardCount") or 0) + 3
    if coverage.get("sectionedExportCount", 0) < expected_section_count:
        errors.append("section export coverage is missing intro, per-burden, restoration, or formal sections")
    section_plan = metrics.get("sectionPlan") or []
    if len(section_plan) < expected_section_count:
        errors.append("rendered section export plan is missing intro, per-burden, restoration, or formal sections")
    if section_plan:
        if section_plan[0].get("type") != "intro":
            errors.append("first sectioned export crop must be the intro section")
        required_types = {"intro", "burden", "restoration", "formal"}
        observed_types = {section.get("type") for section in section_plan}
        missing_types = sorted(required_types - observed_types)
        if missing_types:
            errors.append(f"sectioned export plan is missing semantic sections: {', '.join(missing_types)}")
        for index, section in enumerate(section_plan):
            crop = section.get("sourceCrop") or {}
            semantic = section.get("semanticBounds") or {}
            crop_top = float(crop.get("y") or section.get("y") or 0)
            crop_bottom = crop_top + float(crop.get("height") or section.get("height") or 0)
            semantic_top = float(semantic.get("top") or semantic.get("y") or 0)
            semantic_bottom = float(semantic.get("bottom") or (semantic_top + float(semantic.get("height") or 0)))
            prev_bottom = section.get("previousSectionBottom")
            next_top = section.get("nextSectionTop")
            if section.get("foreignSectionOverlap"):
                errors.append(f"section crop overlaps a neighboring semantic section: {section.get('file') or section.get('name')}")
            if not section.get("canvasSafe", False):
                errors.append(f"section crop is not marked canvas-safe: {section.get('file') or section.get('name')}")
            if prev_bottom is not None and crop_top < float(prev_bottom) - 0.5:
                errors.append(f"section crop starts before previous semantic boundary: {section.get('file') or section.get('name')}")
            if next_top is not None and crop_bottom > float(next_top) + 0.5:
                errors.append(f"section crop crosses into the next semantic boundary: {section.get('file') or section.get('name')}")
            if crop_top > semantic_top + 0.5 or crop_bottom < semantic_bottom - 0.5:
                errors.append(f"section crop clips its own semantic section: {section.get('file') or section.get('name')}")
            if section.get("type") == "intro" and next_top is not None and crop_bottom > float(next_top) + 0.5:
                errors.append("intro sectioned export crop includes the first burden boundary")
            if (
                section.get("type") == "restoration"
                and index + 1 < len(section_plan)
                and section_plan[index + 1].get("type") == "formal"
                and crop_bottom > float(section_plan[index + 1].get("semanticBounds", {}).get("top") or next_top or crop_bottom) + 0.5
            ):
                errors.append("restoration sectioned export crop includes the formal appendix")
    if coverage.get("pngHeight", 0) < coverage.get("paddedExportHeight", 0) * 0.70:
        errors.append("PNG export height is suspiciously shorter than the measured content height")
    bottom_padding = coverage.get("bottomPadding")
    if bottom_padding is None or bottom_padding < GLOBAL_BOTTOM_PADDING_MIN:
        errors.append("exported SVG does not preserve bottom padding after the final content")
    if bottom_padding is not None and bottom_padding > GLOBAL_BOTTOM_PADDING_MAX:
        errors.append(f"rendered SVG has excessive post-legend bottom padding ({bottom_padding}px)")
    post_terminal_padding = coverage.get("postTerminalCardBottomPadding")
    if post_terminal_padding is not None and post_terminal_padding > POST_TERMINAL_BOTTOM_PADDING_MAX:
        errors.append(f"rendered SVG has excessive post-terminal-card bottom padding ({post_terminal_padding}px)")
    exported_bottom_padding = coverage.get("exportedBottomPadding")
    if exported_bottom_padding is not None and exported_bottom_padding < EXPORTED_BOTTOM_PADDING_MIN:
        errors.append(f"exported SVG bottom padding is too tight ({exported_bottom_padding}px)")
    if exported_bottom_padding is not None and exported_bottom_padding > EXPORTED_BOTTOM_PADDING_MAX:
        errors.append(f"exported SVG has excessive bottom padding ({exported_bottom_padding}px)")
    if coverage.get("exportedBurdenCardCount") != coverage.get("burdenCardCount"):
        errors.append("exported burden-card count does not match rendered burden-card count")
    if metrics.get("restorativeResponseCount", 0) < 1:
        errors.append("rendered story view did not include the body-prose Restorative Response card")
    if metrics.get("closingFormulationCount", 0) < 1:
        errors.append("rendered story view did not include the body-prose Closing Formulation card")
    if metrics.get("formalCaseFillCount", 0) != 0:
        errors.append("default story view should keep Formal Case Fill out of the public map")
    if not coverage.get("canvasSafe", False) and "function exportPngSections" not in JS.read_text(encoding="utf-8"):
        errors.append("one-shot PNG exceeds safe canvas limits and no sectioned export fallback exists")
    for row in metrics.get("routeRows", []):
        text = row.get("text", "")
        if re.fullmatch(r"(?:RECURSE|STOP|HOLD|LoopBreak)\s*", text, re.I):
            errors.append(f"route row is low-information: {text!r}")
        if row.get("innerTextWidth", 0) < row.get("width", 0) * 0.70:
            errors.append("route row reserves too much non-text width")
    for row in metrics.get("submoves", []):
        if row.get("innerTextWidth", 0) < row.get("width", 0) * 0.90:
            errors.append("submove text wrapper is materially narrower than the card width")
    for row in metrics.get("bottomPaddingPanels", []):
        bottom = float(row.get("bottomPadding") or 0)
        height = float(row.get("height") or 0)
        if height > 160 and (bottom > 120 or bottom > height * 0.35):
            errors.append(
                "content card has excessive bottom padding "
                f"({bottom:.1f}px of {height:.1f}px): {row.get('text', '')!r}"
            )
    for row in metrics.get("terminalBottomPadding", []):
        bottom = float(row.get("bottomPadding") or 0)
        text = row.get("text", "")
        if bottom < TERMINAL_BOTTOM_PADDING_MIN or bottom > TERMINAL_BOTTOM_PADDING_MAX:
            errors.append(
                "terminal/footer card bottom padding is outside the allowed range "
                f"({bottom:.1f}px): {text!r}"
            )


def main() -> int:
    errors: list[str] = []
    for path in (JS, CSS, SECTION):
        if not path.exists():
            errors.append(f"{rel(path)} is missing")
    if errors:
        print("output grapher layout check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    js_text = JS.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")
    section_text = SECTION.read_text(encoding="utf-8")
    story_body = render_story_body(js_text)

    required_js = {
        "dynamic story panels": "storySectionBlock",
        "dynamic restoration panel": "renderCollapsePanel(model,x,y,w)",
        "formal case fill renderer": "function renderFormalCaseFill",
        "visible task anchor": "Task stated in the output",
        "plain conclusion anchor": "Final Answer From The Output",
        "visible claim context resolver": "function visibleClaimContext(model)",
        "large case headline": "function storyCaseHeadline(model)",
        "case headline rendered": "CASE: Trinitarian reply to John 17:3",
        "case map badge": "What this map is about",
        "Trinitarian visible context": "A Trinitarian reply",
        "Trinitarian verdict headline": "the Trinitarian reply fails to close the John 17:3 objection",
        "restorative noetic title": "Output grapher — Restorative Noetic Map",
        "closing formulation extraction": "model.closingFormulation",
        "formal case fill class": "outputGrapherFormalCaseFill",
        "visible final prose cleaner": "function cleanVisibleProseBlock",
        "visible final section extractor": "function extractBodySection",
        "final body prose renderer": "function renderFinalProseCard",
        "restorative response card": "outputGrapherRestorativeResponse",
        "closing formulation card": "outputGrapherClosingFormulation",
        "shared SVG card header": "function renderCardHeader",
        "shared SVG header badges": "function renderHeaderBadges",
        "top-right panel badges": "renderHeaderBadges(badgeItems,x+pad,badgeY,contentW,'right')",
        "badge-reserved title width": "const titleW=badgeW?",
        "pixel-estimated SVG text width": "function estimateSvgTextWidth",
        "shared SVG text wrapper": "function wrapSvgText",
        "story pixel wrapper": "function storyWrap",
        "header height return": "bodyY:y+headerHeight+24",
        "section cards use shared header": "const header=renderCardHeader({x,y,width:w,title,badges,color,titleSize,pad,titleWeight:720})",
        "MRP header badge": "badges:[{label:`MRP(${b})`",
        "short land panel title": "What this establishes",
        "short reread panel title": "After this, what remains?",
        "short MRP panel title": "Follow-up: pressure-check",
        "compact route row renderer": "function renderRouteRow",
        "compact route row class": "outputGrapherRouteRow",
        "route badge top-right metadata": 'data-route-badge-position="top-right"',
        "burden problem subtitle": "subtitle:problemText",
        "dynamic submove cards": "moveBlocks=sms.map",
        "dynamic submove height": "return {title:heading,sections:measured,height:Math.max(d.subMinH,height+8)}",
        "submove section measurement": "function measureSubmoveSections(sections,w,d)",
        "submove body section cards": "bodySubmoveSections(model,sm,node)",
        "summary-first field text": "function storyFieldText(text,label='')",
        "submove differentiated renderer": "renderSubmoveSections(block",
        "label/value split support": "function splitLeadingLabel(text)",
        "submove readable label scale": "const labelSize=Math.max(21,d.font)",
        "submove readable body scale": "const bodySize=Math.max(22,d.font)",
        "submove target/result support": "['Target', details.target]",
        "submove semibold labels only": "'#bae6fd',section.labelSize,690",
        "story body regular weight": "'#e5e7eb',bodySize,540",
        "story technical muted weight": "'#94a3b8',techSize,500",
        "MRP row breathing gap": "const rowGap=22",
        "MRP row internal padding": "const rowPad=14",
        "MRP row semibold labels": 'font-weight="700"',
        "MRP row body regular weight": "bodyFill,bodySize,bodyWeight",
        "technical row lighter weight": "const bodyWeight=/^Technical$/i.test(row.label)?480:500",
        "route next-step resolver": "routePanelItems(model,b,nextBurden,routes,result)",
        "route with next burden": "Move to next identified problem:",
        "route row body text width metadata": "data-inner-text-width=\"${textW}\"",
        "structured MRP panel rows": "mrpPanelRows(model,b,result,edgeText,routes,rereadText)",
        "content-aware route row": "const bottomRowH=mrpBlock.height+18+(mrpSourceBlock.svg?mrpSourceBlock.height+18:0)+routeBlock.height",
        "MRP panel uses full story width": "bottomPanelY,fullW",
        "padded export clone": "function cloneSvgForExport",
        "minimum body font": "bodySize=16",
        "minimum technical font": "techSize=16",
        "large burden title": "titleSize:34",
        "list block rendering": "function storyListBlock",
        "rectangular view badge": 'height="44" rx="9"',
        "story legend route color": "next issue / HOLD / RECURSE",
        "story legend closed color": "STOP / closed / restoration",
        "desktop story width": "const width=1800",
        "actual panel width wrapping": "storyWrap(subtitle||'not detected', innerW, bodySize",
        "output zone split": "function splitOutputZones",
        "source-section detector": "function detectSourceSections",
        "source-section coverage manifest": "function sourceCoverageManifest",
        "source coverage manifest field": "sourceCoverage:sourceCoverageManifest",
        "source setup cards": "outputGrapherSourceSetup",
        "source-section render layer classifier": "sourceRenderLayer",
        "technical source coverage appendix": "outputGrapherSourceCoverageAppendix",
        "public structure digest": "function publicStructureDigest",
        "closure witness source card": "outputGrapherClosureWitnessSource",
        "body prose extraction": "bodyExtract",
        "canonical public notation": "function canonicalizePublicNotation",
        "visible submove details": "submoveDetails",
        "body-first land text": "bodyLandText(model,b,land)",
        "body-first reread text": "bodyRereadText(model,b,reread)",
        "list-like remaining items": "function splitListLikeItems",
        "PNG export sizing": "function pngExportConfig",
        "sectioned PNG fallback": "function exportPngSections",
        "section ZIP creator": "function createZipBlob",
        "section PNG renderer": "function renderPngBlobFromSvgNode",
        "section export manifest": "function sectionExportManifest",
        "semantic section anchors": "data-og-section=\"intro\"",
        "semantic burden anchors": "data-og-section=\"burden\"",
        "semantic restoration anchor": "data-og-section=\"restoration\"",
        "semantic formal anchor": "data-og-section=\"formal\"",
        "semantic section collector": "function storySemanticSections",
        "section boundary manifest previous": "previousSectionBottom",
        "section boundary manifest next": "nextSectionTop",
        "section overlap manifest": "foreignSectionOverlap",
        "font-ready export wait": "function waitForExportLayout",
        "section export plan API": "sectionExportPlan",
        "section ZIP export filename": "daee-output-grapher-sections.zip",
        "section manifest file": "manifest.json",
        "export coverage report": "function exportCoverageReport",
        "restorative export coverage": "hasRestorativeResponse",
        "closing export coverage": "hasClosingFormulation",
        "formal export coverage": "hasFormalCaseFill",
        "poster PNG mode": "poster:2200",
        "visible-output task copy": "Task stated in the output",
        "visible-output pressure copy": "Structural pressure from the visible output",
        "visible-output restoration copy": "Restoration aim from the output",
        "technical diagnosis demoted": "technicalDiagnosis(model)",
    }
    for label, token in required_js.items():
        if token not in js_text:
            errors.append(f"{rel(JS)} missing {label}: {token!r}")

    forbidden_story = {
        "fixed panel height": "panelH",
        "fixed burden story floor": "Math.max(720",
        "fixed submove story height": "d.subH",
        "decorative mini-flow call": "storyMiniFlow(model",
        "story mini toggle": "d.mini",
        "giant SVG pill styling": 'rx="999"',
        "body text balance wrapping": "text-wrap: balance",
        "aggressive body word breaking": "word-break:",
        "insider field diagnosis as main copy": "Field diagnosis:",
        "insider case recognized as main copy": "Case recognized:",
        "insider claim pattern as main copy": "Claim pattern:",
        "insider hidden structure as main copy": "Hidden structure:",
        "synthetic essay summary": "The output breaks the reply",
        "synthetic case commentary": "A theological defense that mixes",
        "synthetic reliance commentary": "It relies on shifting key terms",
        "old story title": "OUTPUT GRAPHER - REBUTTAL MAP",
        "in-flow reader guide title": "How to read this map",
        "obsolete reader guide renderer": "function readingGuideItems",
        "technical proof strip inside restoration": "Technical proof strip",
        "duplicate Land technical line": "technical:`Land(${b})`",
        "duplicate reread technical line": "technical:'R(H,Δ)'",
        "long land panel title": "What this establishes against the reply",
        "long reread panel title": "After this answer, what remains?",
        "long MRP panel title": "Follow-up: does the reply still have pressure?",
        "left route badge text column": "textX=x+pad+badgeW+22",
        "raw failure-point issue labels": "function issueLabel(b){return `Failure point",
        "raw old issue title": "${issueLabel(b)} - ",
        "repeated story badge chrome": "parts.push(storyBadge",
        "empty route panel": "storySectionBlock('Next issue / closure',humanize(routes)",
        "large route card renderer": "const routeBlock=storySectionBlock(routeClosed?'Closure route':'Next step'",
        "burden header terminal badge": "const statusBadge=publicTerminalBadge",
        "burden header route badge": "const routeBadge=publicRouteBadge",
        "burden header status badge injection": "{label:statusBadge",
        "burden header route badge injection": "{label:routeBadge",
        "detached section left rail": 'width="7" height="${height}"',
        "detached submove left rail": 'width="8" height="${block.height}"',
        "detached burden left rail": 'width="10" height="${cardH}"',
        "thick submove top strip": 'height="6" rx="6" fill="#38bdf8"',
        "paint-stroke submove top rule": 'stroke-linecap="round" opacity=".72"',
        "pill story top accent": 'height="7" rx="7" fill="${rail}"',
        "pill burden top accent": 'height="8" rx="8" fill="#3b82f6"',
        "decorative top accent rectangle": 'height="3" fill=',
        "density-mode state": "currentDensity",
        "density config": "densityConfig",
        "density controls": "data-og-density",
        "hidden submove count": "hiddenCount",
        "visible submove slice": "visibleSms",
        "sentence-limited submove prose": "firstSentences",
        "inspector truncation marker": "(more in inspector)",
        "character-count story wrapper": "function storyLineChars",
        "old width-to-character story wrapping": "width/(size*",
    }
    for label, token in forbidden_story.items():
        if token in story_body:
            errors.append(f"{rel(JS)} story view still contains {label}: {token!r}")

    forbidden_css = {
        "content-card clipping": r"outputGrapher(?:Story|Top|Graph|Inspector|Restoration)[^{]*\{[^}]*overflow\s*:\s*hidden",
        "fixed burden card height": r"\.outputGrapherStoryBurden[^{]*\{[^}]*height\s*:",
        "fixed story panel height": r"\.outputGrapherStoryPanel[^{]*\{[^}]*height\s*:",
        "giant pill CSS styling": r"border-radius\s*:\s*999px",
        "density control styling": r"outputGrapherDensity",
    }
    for label, pattern in forbidden_css.items():
        if re.search(pattern, css_text, re.I | re.S):
            errors.append(f"{rel(CSS)} contains {label}")

    required_css = {
        "visible grapher overflow": ".outputGrapher{overflow:visible}",
        "reader-size top-card text": "font-size:16px",
        "reader-size inspector": "font-size:16px",
        "route legend swatch": ".ogRoute{background:#f59e0b}",
        "closed legend swatch": ".ogClosed{background:#10b981}",
        "responsive top cards": ".outputGrapherTopCards,.outputGrapherMapScope{grid-template-columns:1fr}",
        "wide graph viewport": ".outputGrapherGraph svg{display:block;min-width:1600px;max-width:none}",
        "export size control styling": ".outputGrapherExportSize",
        "collapsed top help styling": ".outputGrapherHelp",
        "map scope styling": ".outputGrapherMapScope",
        "primary map label styling": ".outputGrapherPrimaryView",
    }
    for label, token in required_css.items():
        if token not in css_text:
            errors.append(f"{rel(CSS)} missing {label}: {token!r}")

    required_section = {
        "route legend label": "next issue / HOLD / RECURSE",
        "closed legend label": "STOP / closed / restoration",
        "PNG desktop size": "Desktop PNG (1800px)",
        "PNG poster size": "Poster PNG (2200px)",
        "PNG compact size": "Compact PNG (1500px)",
        "sectioned PNG export button": "ogExportPngSectionsBtn",
        "section ZIP export label": "Export section ZIP",
        "single full output input": "Paste full daee-epistemics output",
        "primary map view label": "Restorative Noetic Map View",
        "map scope support": "What the Restorative Noetic Map shows",
        "top help control": "outputGrapherHelp",
        "top help label": "How to read this",
    }
    for label, token in required_section.items():
        if token not in section_text:
            errors.append(f"{rel(SECTION)} missing {label}: {token!r}")

    if errors:
        print("output grapher layout check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    rendered_layout_check(errors)
    if errors:
        print("output grapher layout check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("output grapher layout check: PASS")
    print(f"- story renderer: {rel(JS)}")
    print(f"- styles: {rel(CSS)}")
    print(f"- section: {rel(SECTION)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
