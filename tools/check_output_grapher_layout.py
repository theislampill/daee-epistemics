#!/usr/bin/env python3
"""Guard the Output Grapher story-view layout against clipped infographic cards."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "index" / "output-grapher.js"
CSS = ROOT / "docs" / "index" / "output-grapher.css"
SECTION = ROOT / "docs" / "index" / "sections" / "output-grapher.html"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def render_story_body(js_text: str) -> str:
    match = re.search(r"function renderStorySvg\(model\)\{(?P<body>.*?)\n  function renderGraph\(model\)\{", js_text, re.S)
    return match.group("body") if match else ""


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
        "plain tested-claim anchor": "Claim under review",
        "plain conclusion anchor": "Final answer from the output",
        "closing formulation extraction": "model.closingFormulation",
        "wrapped burden title measurement": "titleLines=wrapWords",
        "badge below measured title": "const badgeY=y+56+titleLines.length*42+18",
        "full problem text measurement": "problemLines=wrapWords",
        "dynamic submove cards": "moveBlocks=visibleSms.map",
        "dynamic submove height": "height:Math.max(d.subMinH,lines.length*d.line+30)",
        "semantic burden rail": 'fill="#3b82f6"',
        "semantic submove rail": 'fill="#38bdf8"',
        "semantic MRP rail": "rail:'#a855f7'",
        "semantic route rail": "rail:routeClosed?'#10b981':'#f59e0b'",
        "comfortable density": "currentDensity='comfortable'",
        "minimum body font": "bodySize=16",
        "minimum technical font": "techSize=16",
        "large burden title": "storyLineText(titleLines,margin+34,y+56,42,'#f8fafc',34,900)",
        "list block rendering": "function storyListBlock",
        "rectangular story badges": 'height="34" rx="8"',
        "rectangular view badge": 'height="44" rx="9"',
        "story legend route color": "next failure / HOLD / RECURSE",
        "story legend closed color": "STOP / closed / restoration",
        "desktop story width": "const width=1800",
        "less aggressive line wrapping": "width/(size*0.44)",
        "output zone split": "function splitOutputZones",
        "body prose extraction": "bodyExtract",
        "body-first land text": "bodyLandText(model,b,land)",
        "body-first reread text": "bodyRereadText(model,b,reread)",
        "list-like remaining items": "function splitListLikeItems",
        "PNG export sizing": "function pngExportConfig",
        "poster PNG mode": "poster:2200",
        "plain dependency copy": "What kind of reply this is",
        "plain reliance copy": "What it relies on",
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
    }
    for label, token in forbidden_story.items():
        if token in story_body:
            errors.append(f"{rel(JS)} story view still contains {label}: {token!r}")

    forbidden_css = {
        "content-card clipping": r"outputGrapher(?:Story|Top|Graph|Inspector|Restoration)[^{]*\{[^}]*overflow\s*:\s*hidden",
        "fixed burden card height": r"\.outputGrapherStoryBurden[^{]*\{[^}]*height\s*:",
        "fixed story panel height": r"\.outputGrapherStoryPanel[^{]*\{[^}]*height\s*:",
        "giant pill CSS styling": r"border-radius\s*:\s*999px",
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
        "responsive top cards": ".outputGrapherTopCards{grid-template-columns:1fr}",
        "wide graph viewport": ".outputGrapherGraph svg{display:block;min-width:1600px;max-width:none}",
        "export size control styling": ".outputGrapherExportSize",
    }
    for label, token in required_css.items():
        if token not in css_text:
            errors.append(f"{rel(CSS)} missing {label}: {token!r}")

    required_section = {
        "route legend label": "next failure / HOLD / RECURSE",
        "closed legend label": "STOP / closed / restoration",
        "comfortable default": 'class="active" data-og-density="comfortable"',
        "PNG desktop size": "Desktop PNG (1800px)",
        "PNG poster size": "Poster PNG (2200px)",
        "PNG compact size": "Compact PNG (1500px)",
    }
    for label, token in required_section.items():
        if token not in section_text:
            errors.append(f"{rel(SECTION)} missing {label}: {token!r}")

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
