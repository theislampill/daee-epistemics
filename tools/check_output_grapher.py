#!/usr/bin/env python3
"""Validate the docs Output Collapse Grapher artifact and fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from output_grapher_lib import graph_html, parse_output, result_summary

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
        "export PNG size selector": "ogExportWidthMode",
        "desktop PNG mode": "Desktop PNG (1800px)",
        "poster PNG mode": "Poster PNG (2200px)",
        "compact PNG mode": "Compact PNG (1500px)",
        "export SVG button": "ogExportSvgBtn",
        "export JSON button": "ogExportJsonBtn",
        "optional Mermaid export": "Export Mermaid",
        "optional Mermaid ELK": "defaultRenderer': 'elk",
        "rebuttal mode": "Rebuttal View",
        "DAG mode": "Technical Pipeline View",
        "validation mode": "Validation View",
        "density controls": "Comfortable",
        "expanded density": "Expanded",
        "density config": "densityConfig",
        "input digest panel": "Reply / Claim Being Rejected",
        "reader-facing input fallback": "readerInputDigest",
        "plain dependency panel": "What The Reply Depends On",
        "burden inventory panel": "Main Problems In The Reply",
        "collapse status panel": "Final Answer From The Output",
        "graph conclusion card": "Final Answer From The Output",
        "plain restoration summary": "Restoration Summary",
        "restoration bullet builder": "restorationBullets",
        "technical proof strip": "Technical proof strip",
        "story view renderer": "renderStorySvg",
        "story burden cards": "outputGrapherStoryBurden",
        "plain claim label": "Reply / claim being rejected",
        "plain conclusion label": "Final answer from the output",
        "plain dependency label": "What the reply depends on",
        "body prose split": "splitOutputZones",
        "visible body extraction": "bodyExtract",
        "body-first canonicalizer": "canonicalizePublicNotation",
        "body submove detail extraction": "submoveDetails",
        "body submove resolver": "bodySubmoveLabel",
        "body-first land panel": "bodyLandText",
        "body-first reread panel": "bodyRereadText",
        "list-like remaining rendering": "splitListLikeItems",
        "plain answer label": "How this problem is answered",
        "plain land label": "What this establishes against the reply",
        "plain reread label": "After this answer, what remains?",
        "plain MRP label": "Follow-up: does the reply still have pressure?",
        "burden cluster container": "outputGrapherBurdenCluster",
        "semantic edge labels": "outputGrapherEdgeLabel",
        "generated burden relation": "new problem surfaced",
        "closure restoration edge": "closure / restoration",
        "inline SVG renderer": "renderGraph",
        "PNG export function": "exportPng",
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
        "field witness as body copy": "field_witness metadata appears as main",
    }
    for label, token in forbidden_public_patterns.items():
        if token in js_text:
            errors.append(f"Output Grapher still has {label}: {token!r}")
    if "bodyExtract.burdenTitles" not in js_text or "bodyExtract.submoveDetails" not in js_text:
        errors.append("Output Grapher must resolve burden/submove display text from visible body prose before witness metadata")
    if "canonicalizePublicNotation(edgeText)" not in js_text:
        errors.append("Output Grapher must canonicalize public graph/resultant text before rendering")
    if "Main Problems In The Reply" in combined and "bodyBurdenDescription(model,b)" not in js_text:
        errors.append("Output Grapher burden inventory must use visible body headings, not witness-only labels")


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
