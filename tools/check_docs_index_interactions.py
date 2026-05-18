"""Check docs/index.html top-level tab interaction wiring.

This is a structural guard for the public control-wiki page. It catches the
regression class where visible tab buttons remain present but their target
panels, ARIA wiring, or JavaScript controller drift out of sync.
"""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"
MANIFEST = ROOT / "docs" / "index" / "manifest.json"
ARCHITECTURE_SECTION = ROOT / "docs" / "index" / "sections" / "architecture.html"
THEORY_SECTION = ROOT / "docs" / "index" / "sections" / "theory.html"
MODULE_CATALOGUE = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "module-catalogue.json"
GENERATED_BANNER = "GENERATED FILE: do not edit this HTML output directly"
ALLOWED_CLASSIFICATIONS = {
    "OWNER_DERIVED",
    "STRUCTURED_SOURCE_DERIVED",
    "CURATED_SUMMARY_WITH_OWNER_REFERENCES",
    "STATIC_SNAPSHOT",
    "LAYOUT_ONLY",
}

EXPECTED_TABS = {
    "Architecture": "architecture",
    "Owners & TTP": "owners",
    "Theory Deep Dive": "theory",
    "Reference Library": "reference",
}

REQUIRED_INDEX_NOTATION_TOKENS = {
    "Architecture controlled row layout": "v60-pipeline-row",
    "Architecture post-Delta field diagnostic node": "∇·T / ∇×T target-explicit diagnostics",
    "Architecture formal field-state node": "ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ → ∇·T/∇×T",
    "Architecture target grammar": "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}",
    "Architecture readable divergence target grammar": "v60-field-target\">∇·T",
    "Architecture readable curl target grammar": "v60-field-target\">∇×T",
    "Architecture divergence route example": "v60-field-target\">∇·route",
    "Architecture curl route example": "v60-field-target\">∇×route",
    "Architecture LoopBreak witness": "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
    "Architecture LoopBreak grounding grammar": "G ∈ {fiṭrah, ʿaql ṣarīḥ, necessary knowledge, definition discipline, direct contradiction exposure, source-status correction}",
    "Architecture COMPLETE closure marker": "✓<br/>COMPLETE",
    "Theory deltaB control card": "goConceptField('deltaB')",
    "Theory deltaK control card": "goConceptField('deltaK')",
    "Theory nabla-dot control card": "goConceptField('nablaDot')",
    "Theory nabla-cross control card": "goConceptField('nablaCross')",
    "Theory route-gradient control card": "goConceptField('gradient')",
    "Theory loop-break control card": "goConceptField('loopBreak')",
    "Theory PsiI control card": "goConceptField('PsiI')",
    "Theory coupling control card": "goConceptField('coupling')",
    "Theory nabla-dot notation token": "data-k=\"nablaDot\"",
    "Theory nabla-cross notation token": "data-k=\"nablaCross\"",
    "Theory route-gradient notation token": "data-k=\"gradient\"",
    "Theory loop-break notation token": "data-k=\"loopBreak\"",
    "Theory PsiI selector": "goConceptField('PsiI')",
    "Theory coupling notation token": "data-k=\"coupling\"",
    "Theory coupling output boundary": "public release boundary",
    "Theory T_lang boundary": "T_lang: Ψᴺ ⇢ Ψᴵ",
    "Concept graph nabla-dot concept": "id:'nablaDot'",
    "Concept graph nabla-cross concept": "id:'nablaCross'",
    "Concept graph del-dot concept": "id:'delDot'",
    "Concept graph del-cross concept": "id:'delCross'",
    "Concept graph del-dot symbol-first name": "name:'∇· / del-dot alias'",
    "Concept graph del-cross symbol-first name": "name:'∇× / del-cross alias'",
    "Concept graph del-dot notation alias type": "name:'∇· / del-dot alias', type:'notation alias'",
    "Concept graph del-cross notation alias type": "name:'∇× / del-cross alias', type:'notation alias'",
    "Concept graph route-gradient concept": "id:'gradient'",
    "Concept graph loop-break concept": "id:'loopBreak'",
    "Concept graph PsiI concept": "id:'PsiI'",
    "Concept graph coupling concept": "id:'coupling'",
    "Relation delta before field diagnostics": "rel-delta-before-field-diagnostics",
    "Relation field diagnostics reread": "rel-field-diagnostics-reread",
    "Relation del-dot alias": "rel-del-dot-alias",
    "Relation del-cross alias": "rel-del-cross-alias",
    "Relation live field gradient": "rel-live-field-gradient",
    "Relation gradient constrained": "rel-gradient-gate-constrained",
    "Relation gradient release pressure": "rel-gradient-selects-release-pressure",
    "Relation curl loop-break": "rel-curl-loopbreak",
    "Relation loop-break reread": "rel-loopbreak-delta-reread",
    "Relation closure field condition": "rel-closure-field-condition",
    "Relation agent/interlocutor coupling": "rel-agent-interlocutor-coupling",
    "Architecture route-gradient": "Gate/routing + ∇ route-gradient",
    "Architecture loop-break": "LoopBreak if ∇×T nonzero",
    "Architecture closure field condition": "𝒞(Ψᴺ)",
    "Architecture language coupling": "T_lang: Ψᴺ ⇢ Ψᴵ",
    "Theory divergence symbol row": "∇·T field diagnostic",
    "Theory curl symbol row": "∇×T field diagnostic",
    "Theory del-dot alias": "del-dot",
    "Theory del-cross alias": "del-cross",
    "Theory alias definition": "checker/grep aliases only",
    "Theory target grammar": "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}",
    "Theory post-Delta field state": "post-Delta ∇·/∇× field-state diagnostics",
    "Burden target example": "∇·ⁿB",
    "Register target example": "∇×ξ",
    "Theory LoopBreak witness": "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
    "Theory LoopBreak grounding grammar": "G ∈ {fiṭrah, ʿaql ṣarīḥ, necessary knowledge, definition discipline, direct contradiction exposure, source-status correction}",
    "Theory phase discipline gradient": "∇ ranks eligible route pressure before release",
    "Theory phase discipline Delta": "Δ produces the changed field state",
    "Theory phase discipline diagnostics": "∇·T / ∇×T diagnose target-explicit post-Δ field pressure",
    "Theory phase discipline reread": "R(H,Δ) rereads the changed field",
    "Theory phase discipline closure": "𝒞(Ψᴺ) licenses closure as field condition",
    "Theory phase discipline coupling": "T_lang: Ψᴺ ⇢ Ψᴵ marks public coupling without guaranteed uptake",
    "No proof by symbol boundary": "not proof-by-symbol",
    "Full bridge classification": 'id="full-register-bridge" data-classification="CURATED_SUMMARY_WITH_OWNER_REFERENCES"',
    "Full bridge register/state components": "1. Register/state components",
    "Full bridge burden cycle": "2. Route-gradient and burden cycle",
    "Full bridge delta transition": "3. Delta transition",
    "Full bridge field diagnostics": "4. Field diagnostics",
    "Full bridge reread and closure": "5. Reread and closure",
    "Full bridge coupling": "6. Coupling and public release",
    "Full bridge non-claims": "7. Non-claims and forbidden uses",
    "Full bridge H held set": "<dt>H</dt>",
    "Full bridge deltaB": "<code>ΔⁿB</code> marks the burden-event delta",
    "Full bridge deltaK": "<code>Δκ</code> marks case-collapse / closure-state change",
    "Full bridge nabla not kappa-only": "but not the only ∇ target",
    "Full bridge nabla-dot definition": "<code>∇·T</code> reads divergence-like residual outward pressure",
    "Full bridge nabla-cross definition": "<code>∇×T</code> reads curl-like circularity",
    "Full bridge del aliases": "checker/grep aliases only",
    "Full bridge R reread": "<code>R(H,Δ)</code> rereads held material",
    "Full bridge selected path boundary": "The selected execution path is the release order over the live field, not the whole field.",
    "Full bridge long exposition boundary": "Long formalism exposition belongs to audit/formalism-expanded render",
    "Full bridge Shannon boundary": "Shannon language is limited to signal/encoding/channel/noise/distortion/redundancy/compression/capacity",
    "Full bridge NLA boundary": "NLA means Natural Language Autoencoder reconstruction fidelity",
    "Full bridge RECURSE example": "²B landed; Δ²B updated; Δκ live; ∇·ⁿB positive over dependent burdens; ∇×ξ unresolved",
    "Full bridge STOP example": "All live burdens landed/integrated/held; Δκ contracted; ∇·κ negative; ∇×κ resolved; 𝒞(Ψᴺ): STOP",
    "Full bridge route-gradient": "∇ route-gradient",
    "Full bridge loop-break": "LoopBreak(∇×T)",
    "Full bridge loop-break witness": "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
    "Full bridge PsiI": "Ψᴵ",
    "Full bridge T_lang": "T_lang: Ψᴺ ⇢ Ψᴵ",
}

EXPECTED_CONTROL_CARD_ORDER = [
    "noetic",
    "D0",
    "Psi",
    "N",
    "τ",
    "σ",
    "heart",
    "ξ",
    "Ω",
    "μ",
    "κ",
    "H",
    "gradient",
    "burden",
    "submoves",
    "deltaB",
    "deltaK",
    "nablaDot",
    "nablaCross",
    "loopBreak",
    "R",
    "C",
    "final",
    "PsiI",
    "coupling",
]

REQUIRED_CONTROL_CARD_COLOR_CLASSES = (
    "phase-input",
    "phase-layer-a",
    "phase-gate",
    "phase-owner-delta",
    "phase-reread-closure",
    "phase-public-boundary",
)

EXPECTED_CONTROL_CARD_PHASES = {
    "D0": "phase-input",
    "noetic": "phase-layer-a",
    "Psi": "phase-layer-a",
    "N": "phase-gate",
    "τ": "phase-gate",
    "σ": "phase-gate",
    "heart": "phase-gate",
    "ξ": "phase-gate",
    "Ω": "phase-gate",
    "μ": "phase-gate",
    "gradient": "phase-gate",
    "burden": "phase-owner-delta",
    "submoves": "phase-owner-delta",
    "deltaB": "phase-owner-delta",
    "nablaDot": "phase-owner-delta",
    "nablaCross": "phase-owner-delta",
    "loopBreak": "phase-owner-delta",
    "κ": "phase-reread-closure",
    "H": "phase-reread-closure",
    "deltaK": "phase-reread-closure",
    "R": "phase-reread-closure",
    "C": "phase-reread-closure",
    "final": "phase-reread-closure",
    "PsiI": "phase-public-boundary",
    "coupling": "phase-public-boundary",
}

REQUIRED_PIPELINE_NOTATION_TOKENS = {
    "Standalone pipeline route-gradient rail": "ROUTE-GRADIENT PRESSURE",
    "Standalone pipeline field diagnostic rail": "∇·T / ∇×T field diagnostics",
    "Standalone pipeline loop-breaking rail": "LOOP-BREAKING SUBMOVE",
    "Standalone pipeline closure-field rail": "𝒞(Ψᴺ) CLOSURE-FIELD CONDITION",
    "Standalone pipeline coupling rail": "T_lang: Ψᴺ ⇢ Ψᴵ",
    "Standalone pipeline Land before Delta": "Land(ⁿB)<br>→ ΔⁿB / Δκ",
    "Standalone pipeline post-Delta wording": "target-explicit post-Delta field diagnostics",
}

FORBIDDEN_INDEX_NOTATION_CLAIMS = {
    "∇ replaces Δ": "∇ replaces Δ",
    "nabla replaces Delta": "nabla replaces delta",
    "divergence proves truth": "divergence proves truth",
    "curl proves warrant": "curl proves warrant",
    "∇ truth metric": "∇ truth metric",
    "∇ warrant metric": "∇ warrant metric",
    "del-dot separate operator": "del-dot is a separate operator",
    "del-cross separate operator": "del-cross is a separate operator",
    "selected path whole field": "selected execution path is the whole field",
    "field diagnostics prove warrant": "field diagnostics prove warrant",
    "gradient bypasses gates": "∇ bypasses gates",
    "gradient replaces Delta": "∇ replaces Δ",
    "LoopBreak arbitrary assertion": "LoopBreak is arbitrary assertion",
    "closure guarantees conversion": "𝒞(Ψᴺ) guarantees conversion",
    "PsiI soul access": "Ψᴵ gives access to the soul",
    "agent controls guidance": "agent controls guidance",
}

TARGET_GRAMMAR = "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}"
LOOPBREAK_WITNESS = "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R"
GROUNDING_GRAMMAR = "G ∈ {fiṭrah, ʿaql ṣarīḥ, necessary knowledge, definition discipline, direct contradiction exposure, source-status correction}"


class IndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[tuple[str, str]] = []
        self.tabs: list[dict[str, str | None]] = []
        self.panels: list[dict[str, str | None | bool]] = []
        self.tablist_seen = False
        self.scripts: list[str] = []
        self._current_tab: dict[str, str | None] | None = None
        self._tab_text: list[str] = []
        self._in_script = False
        self._script_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if "id" in attr and attr["id"]:
            self.ids.append((tag, attr["id"]))
        if tag == "div" and "tabs" in classes and attr.get("role") == "tablist":
            self.tablist_seen = True
        if tag == "button" and "tab" in classes:
            self._current_tab = {
                "id": attr.get("id"),
                "class": attr.get("class"),
                "data-tab": attr.get("data-tab"),
                "aria-controls": attr.get("aria-controls"),
                "role": attr.get("role"),
                "aria-selected": attr.get("aria-selected"),
                "tabindex": attr.get("tabindex"),
            }
            self._tab_text = []
        if tag == "section" and "tabsec" in classes:
            self.panels.append(
                {
                    "id": attr.get("id"),
                    "class": attr.get("class"),
                    "role": attr.get("role"),
                    "aria-labelledby": attr.get("aria-labelledby"),
                    "hidden": "hidden" in attr,
                }
            )
        if tag == "script":
            self._in_script = True
            self._script_text = []

    def handle_data(self, data: str) -> None:
        if self._current_tab is not None:
            self._tab_text.append(data)
        if self._in_script:
            self._script_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._current_tab is not None:
            self._current_tab["label"] = " ".join("".join(self._tab_text).split())
            self.tabs.append(self._current_tab)
            self._current_tab = None
            self._tab_text = []
        if tag == "script" and self._in_script:
            self.scripts.append("".join(self._script_text))
            self._in_script = False
            self._script_text = []


def run_node_syntax_check(scripts: list[str], errors: list[str]) -> None:
    node = shutil.which("node")
    if not node:
        print("docs/index.html: node not found; skipped JavaScript syntax check")
        return

    with tempfile.TemporaryDirectory(prefix="docs-index-js-") as tmp:
        tmp_path = Path(tmp)
        for index, script in enumerate(scripts):
            path = tmp_path / f"script-{index}.js"
            path.write_text(script, encoding="utf-8")
            proc = subprocess.run(
                [node, "--check", str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout).strip().splitlines()
                first = detail[0] if detail else "syntax check failed"
                errors.append(f"script {index}: JavaScript syntax error: {first}")


def expected_modules(errors: list[str]) -> list[dict[str, str]]:
    if not MODULE_CATALOGUE.exists():
        errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: missing module catalogue owner")
        return []
    try:
        payload = json.loads(MODULE_CATALOGUE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: JSON parse error: {exc}")
        return []
    modules = payload.get("modules")
    if not isinstance(modules, list):
        errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: expected top-level modules list")
        return []
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in modules:
        if not isinstance(entry, dict):
            errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: malformed module entry {entry!r}")
            continue
        module_id = entry.get("id")
        module_class = entry.get("module_class")
        path = entry.get("path")
        if not all(isinstance(value, str) and value for value in (module_id, module_class, path)):
            errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: module entry missing id/path/module_class")
            continue
        if module_id in seen:
            errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: duplicate module id {module_id!r}")
        seen.add(module_id)
        source_path = ROOT / "atomics" / path
        if not source_path.exists():
            errors.append(f"{MODULE_CATALOGUE.relative_to(ROOT)}: module source path missing: {source_path.relative_to(ROOT)}")
        normalized.append(
            {
                "id": module_id,
                "module_class": module_class,
                "path": path,
                "source_path": source_path.relative_to(ROOT).as_posix(),
            }
        )
    return sorted(normalized, key=lambda item: (item["module_class"], item["id"]))


def expand_manifest_path(raw_path: str, errors: list[str]) -> list[Path]:
    if raw_path.endswith("/**"):
        base = ROOT / raw_path[:-3]
        if not base.exists() or not base.is_dir():
            errors.append(f"manifest declared directory missing: {raw_path}")
            return []
        matches = sorted(path for path in base.rglob("*") if path.is_file())
        if not matches:
            errors.append(f"manifest declared directory has no files: {raw_path}")
        return matches
    if any(token in raw_path for token in ("*", "?", "[")):
        matches = sorted(path for path in ROOT.glob(raw_path) if path.is_file())
        if not matches:
            errors.append(f"manifest declared pattern matched no files: {raw_path}")
        return matches
    path = ROOT / raw_path
    if not path.exists():
        errors.append(f"manifest declared path missing: {raw_path}")
        return []
    if path.is_dir():
        return sorted(child for child in path.rglob("*") if child.is_file())
    return [path]


def manifest_paths(entry: dict[str, object]) -> list[str]:
    values: list[str] = []
    for key in ("owner_sources", "freshness_dependencies", "canonical_sources"):
        raw = entry.get(key)
        if isinstance(raw, list):
            values.extend(value for value in raw if isinstance(value, str))
    return values


def check_manifest(errors: list[str]) -> dict[str, object]:
    if not MANIFEST.exists():
        errors.append("docs/index/manifest.json missing")
        return {}
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"docs/index/manifest.json JSON parse error: {exc}")
        return {}
    if manifest.get("schema_version") != 1:
        errors.append("docs/index/manifest.json schema_version must be 1")
    for key in ("output", "template"):
        value = manifest.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"manifest missing {key}")
        else:
            expand_manifest_path(value, errors)
    for value in (manifest.get("derived_data") or {}).values():
        if isinstance(value, str):
            expand_manifest_path(value, errors)
    for index, tab in enumerate(manifest.get("tabs") or []):
        if not isinstance(tab, dict):
            errors.append(f"manifest tabs[{index}] must be an object")
            continue
        classification = tab.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"manifest tabs[{index}] has invalid classification {classification!r}")
        if tab.get("id") != tab.get("panel"):
            errors.append(f"manifest tabs[{index}] panel must match id for current renderer")
        section_source = tab.get("section_source")
        if not isinstance(section_source, str) or not section_source:
            errors.append(f"manifest tabs[{index}] missing section_source")
        else:
            expand_manifest_path(section_source, errors)
        for path in manifest_paths(tab):
            expand_manifest_path(path, errors)
        for block_index, block in enumerate(tab.get("generated_blocks") or []):
            if not isinstance(block, dict):
                errors.append(f"manifest tabs[{index}].generated_blocks[{block_index}] must be an object")
                continue
            if block.get("classification") not in ALLOWED_CLASSIFICATIONS:
                errors.append(f"manifest generated block {block.get('id')!r} has invalid classification")
            owner_source = block.get("owner_source")
            if isinstance(owner_source, str):
                expand_manifest_path(owner_source, errors)
            if block.get("classification") == "OWNER_DERIVED" and not block.get("provider"):
                errors.append(f"manifest owner-derived block {block.get('id')!r} missing provider")
    for index, block in enumerate(manifest.get("visible_blocks") or []):
        if not isinstance(block, dict):
            errors.append(f"manifest visible_blocks[{index}] must be an object")
            continue
        if block.get("classification") not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"manifest visible block {block.get('id')!r} has invalid classification")
        current_source = block.get("current_source")
        if isinstance(current_source, str) and current_source:
            expand_manifest_path(current_source, errors)
        else:
            errors.append(f"manifest visible block {block.get('id')!r} missing current_source")
        for path in manifest_paths(block):
            expand_manifest_path(path, errors)
        if block.get("classification") == "OWNER_DERIVED" and not block.get("provider"):
            errors.append(f"manifest owner-derived visible block {block.get('id')!r} missing provider")
    for index, page in enumerate(manifest.get("standalone_pages") or []):
        if not isinstance(page, dict):
            errors.append(f"manifest standalone_pages[{index}] must be an object")
            continue
        if page.get("classification") not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"manifest standalone page {page.get('id')!r} has invalid classification")
        for key in ("output", "template"):
            value = page.get(key)
            if isinstance(value, str) and value:
                expand_manifest_path(value, errors)
            else:
                errors.append(f"manifest standalone page {page.get('id')!r} missing {key}")
        for path in manifest_paths(page):
            expand_manifest_path(path, errors)
    return manifest


def embedded_modules(text: str, errors: list[str]) -> list[dict[str, str]]:
    match = re.search(r"window\.DOCS_INDEX_MODULE_CATALOGUE\s*=\s*(\[.*?\]);", text, flags=re.S)
    if not match:
        errors.append("generated module catalogue data missing from docs/index.html")
        return []
    try:
        modules = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        errors.append(f"generated module catalogue data is not valid JSON: {exc}")
        return []
    if not isinstance(modules, list):
        errors.append("generated module catalogue data must be a list")
        return []
    normalized: list[dict[str, str]] = []
    for entry in modules:
        if not isinstance(entry, dict):
            errors.append(f"generated module catalogue entry is malformed: {entry!r}")
            continue
        normalized.append({key: str(entry.get(key, "")) for key in ("id", "module_class", "path", "source_path")})
    return sorted(normalized, key=lambda item: (item["module_class"], item["id"]))


def run_generation_freshness_check(errors: list[str]) -> None:
    if not MANIFEST.exists():
        errors.append("docs/index/manifest.json missing; docs/index.html must be generator-backed")
        return
    proc = subprocess.run(
        [sys.executable, "tools/build_docs_index.py", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr).strip()
        errors.append(f"docs index generation freshness failed: {detail}")


def check_notation_contract(text: str, errors: list[str]) -> None:
    for label, token in REQUIRED_INDEX_NOTATION_TOKENS.items():
        if token not in text:
            errors.append(f"docs/index.html missing notation token: {label}: {token!r}")
    lower = text.lower()
    if "κ-only" in lower and "not κ-only" not in lower:
        errors.append("docs/index.html contains κ-only wording without the not-κ-only boundary")
    if "∇· / del-dot" in text and "∇× / del-cross" not in text:
        errors.append("docs/index.html defines del-dot without paired del-cross")
    if "∇× / del-cross" in text and "∇· / del-dot" not in text:
        errors.append("docs/index.html defines del-cross without paired del-dot")
    if 'data-label="∇· / del-dot:' in text or 'data-label="∇× / del-cross:' in text:
        errors.append("Runtime notation data-labels must use ∇·/∇× symbols without ASCII alias prefixes")
    stale_annex_markers = (
        "DSL/IR implementation recommendation",
        "Human interpretability recommendation",
        "Agentic LLM interpretability recommendation",
        "Final recommended notation",
        "current graphic should preserve",
    )
    for marker in stale_annex_markers:
        if marker in text:
            errors.append(f"docs/index.html contains stale proposal-era annex wording: {marker}")
    for label, phrase in FORBIDDEN_INDEX_NOTATION_CLAIMS.items():
        normalized_phrase = phrase.lower()
        if normalized_phrase in lower and f"not {normalized_phrase}" not in lower:
            errors.append(f"docs/index.html contains forbidden notation claim: {label}")


def check_public_notation_surface(path: Path, text: str, errors: list[str]) -> None:
    label = path.relative_to(ROOT).as_posix()
    for token_name, token in (
        ("∇·T target grammar", "∇·T"),
        ("∇×T target grammar", "∇×T"),
        ("target set grammar", TARGET_GRAMMAR),
        ("LoopBreak witness form", LOOPBREAK_WITNESS),
        ("LoopBreak grounding grammar", GROUNDING_GRAMMAR),
    ):
        if token not in text:
            errors.append(f"{label} missing public notation surface token: {token_name}: {token!r}")
    if all(token in text for token in ("∇·κ", "∇·B", "∇·♥")) and TARGET_GRAMMAR not in text:
        errors.append(f"{label} exposes only the old narrow ∇·κ/∇·B/∇·♥ examples without ∇·T target grammar")
    if all(token in text for token in ("∇×κ", "∇×B", "∇×ξ")) and TARGET_GRAMMAR not in text:
        errors.append(f"{label} exposes only the old narrow ∇×κ/∇×B/∇×ξ examples without ∇×T target grammar")


def check_theory_control_cards(text: str, errors: list[str]) -> None:
    start = text.find('<div class="controlOverviewGrid">')
    end = text.find('<div class="notationBoard"', start)
    if start == -1 or end == -1 or end <= start:
        errors.append("docs/index.html missing Theory control ontology card grid")
        return

    block = text[start:end]
    cards = re.findall(
        r"<button\s+class=\"([^\"]*controlCard[^\"]*)\"\s+onclick=\"goConceptField\('([^']+)'\)\"",
        block,
    )
    found = [concept for _classes, concept in cards]
    if found != EXPECTED_CONTROL_CARD_ORDER:
        errors.append(
            "Theory control ontology cards must render in pipeline order: "
            f"expected {EXPECTED_CONTROL_CARD_ORDER!r}, found {found!r}"
        )

    for css_class in REQUIRED_CONTROL_CARD_COLOR_CLASSES:
        if not re.search(rf"\.controlCard\.{re.escape(css_class)}\s*\{{[^}}]*--c\s*:", text, flags=re.S):
            errors.append(f"Theory control card class .controlCard.{css_class} must define --c color")

    class_by_concept = {concept: set(classes.split()) for classes, concept in cards}
    for concept, phase_class in EXPECTED_CONTROL_CARD_PHASES.items():
        if phase_class not in class_by_concept.get(concept, set()):
            errors.append(f"Theory control card {concept!r} must map to {phase_class}")
    if "phase-gate" in class_by_concept.get("nablaDot", set()) or "phase-gate" in class_by_concept.get("nablaCross", set()):
        errors.append("∇·T and ∇×T cards must not map to gate/routing phase")
    if "phase-owner-delta" in class_by_concept.get("gradient", set()):
        errors.append("plain ∇ route-gradient card must not map to owner/Delta diagnostic phase")
    for concept in ("nablaDot", "nablaCross", "loopBreak"):
        if "phase-owner-delta" not in class_by_concept.get(concept, set()):
            errors.append(f"{concept} must map to owner + Δ + diagnostics phase")
    for concept in ("PsiI", "coupling"):
        if "phase-public-boundary" not in class_by_concept.get(concept, set()):
            errors.append(f"{concept} must map to public restorative boundary phase")

    if "name:'del-dot ASCII alias'" in text or "name:'del-cross ASCII alias'" in text:
        errors.append("Concept graph alias cards must lead with ∇·/∇× symbols, not ASCII names")
    if "v60-alias-line" in text or "del-dot = ∇·" in text or "del-cross = ∇×" in text:
        errors.append("Runtime notation must not render ASCII alias equations as pipeline/formula steps")
    if "name:'T_lang language-mediated coupling'" in text:
        errors.append("T_lang concept card must name the output-boundary role explicitly")


def check_pipeline_notation_contract(page_text: str, output: str, errors: list[str]) -> None:
    for label, token in REQUIRED_PIPELINE_NOTATION_TOKENS.items():
        if token not in page_text:
            errors.append(f"{output} missing notation token: {label}: {token!r}")


def main() -> int:
    errors: list[str] = []
    if not INDEX.exists():
        print(f"{INDEX}: missing")
        return 1

    manifest = check_manifest(errors)
    text = INDEX.read_text(encoding="utf-8")
    if GENERATED_BANNER not in text:
        errors.append("docs/index.html missing generated-file banner")
    architecture_start = text.find('id="architecture"')
    runtime_start = text.find('id="canonical-architecture-runtime"', architecture_start)
    if architecture_start == -1:
        errors.append("architecture panel missing from generated index")
    elif runtime_start == -1:
        errors.append("architecture panel must include canonical-architecture-runtime")
    else:
        for marker in ('id="architecture-thesis"', 'class="hero"'):
            marker_pos = text.find(marker, architecture_start)
            if marker_pos != -1 and marker_pos < runtime_start:
                errors.append(
                    "architecture landing must be map-first: "
                    f"{marker} appears before canonical-architecture-runtime"
                )
        flow_pos = text.find('aria-label="Canonical runtime spine"', runtime_start)
        stages_pos = text.find('class="v21-five-col"', runtime_start)
        if flow_pos == -1 or (stages_pos != -1 and flow_pos > stages_pos):
            errors.append("architecture landing must show canonical runtime spine before stage cards")
        runtime_end = text.find('id="architecture-runtime-notes"', runtime_start)
        runtime_slice = text[runtime_start:runtime_end if runtime_end != -1 else len(text)]
        if "STOP/HOLD/RECURSE/PARTIAL/COMPLETE" not in runtime_slice:
            errors.append("architecture runtime spine must render the full closure decision set without spacing-heavy overflow text")
        if "Restorative + T_lang</span>" not in runtime_slice:
            errors.append("architecture runtime spine final chip must use the compact non-clipping T_lang label")
        if "DRY here means" in runtime_slice:
            errors.append("architecture click hint must not expose internal DRY/refactor language")
        stage_color_contract = {
            ".v21-s1": "--sc:var(--blue)",
            ".v21-s2": "--sc:var(--cyan)",
            ".v21-s3": "--sc:var(--violet)",
            ".v21-s4": "--sc:var(--orange)",
            ".v21-s5": "--sc:var(--red)",
        }
        for selector, token in stage_color_contract.items():
            css_token = f"#architecture #canonical-architecture-runtime {selector}"
            if css_token not in text or token not in text[text.find(css_token): text.find(css_token) + 160]:
                errors.append(f"architecture stage card {selector} must match the canonical spine color token {token}")
        row_css = "#architecture #canonical-architecture-runtime .v60-pipeline-row"
        row_css_start = text.find(row_css)
        if row_css_start == -1 or "flex-wrap:wrap!important" not in text[row_css_start: row_css_start + 260]:
            errors.append("architecture runtime spine rows must wrap instead of clipping long chips")
        runtime_row_node_css = "#architecture #canonical-architecture-runtime .v60-runtime-row .node"
        runtime_row_node_start = text.find(runtime_row_node_css)
        if runtime_row_node_start == -1 or "font-size:clamp(11px,.68vw,12px)!important" not in text[runtime_row_node_start: runtime_row_node_start + 260]:
            errors.append("architecture wide runtime spine text must stay in the readable 11-12px range")
        if 'data-substage-key="reread-gate"' not in runtime_slice or '<h3>Reread gate</h3>' not in runtime_slice:
            errors.append("architecture card 4 must mark the Reread gate with the green reread phase")
        if 'data-substage-key="decision"' not in runtime_slice or '<h3>Decision</h3>' not in runtime_slice:
            errors.append("architecture card 4 must mark the Decision block with the green reread phase")
        if ".v60-reread-phase" not in text or "--sc:var(--green)" not in text[text.find(".v60-reread-phase"): text.find(".v60-reread-phase") + 220]:
            errors.append("architecture reread phase styling must use the green phase token")
        expected_substage_keys = [
            "encoded-signal",
            "no-direct-rebuttal",
            "proper-functional-read",
            "structural-registers",
            "operational-boundary",
            "diagnostic-reduction-order",
            "ir-control-surface",
            "gate-owner-layerb",
            "operator-signature",
            "strict-burden-cycle",
            "reread-gate",
            "decision",
            "constrained-resolution",
            "coupling-boundary",
        ]
        for key in expected_substage_keys:
            if f'data-substage-key="{key}"' not in runtime_slice:
                errors.append(f"architecture sub-card must expose clickable data-substage-key={key}")
            if f"'{key}':" not in text and f"{key}:" not in text:
                errors.append(f"architecture sub-card trace map missing {key}")
        if "SUBSTAGE_MAP" not in text or "renderStaticSubstage" not in text:
            errors.append("architecture sub-cards must render their own audit traces")
        if ".v60-selectable-subcard" not in text or "v60-subactive" not in text:
            errors.append("architecture sub-cards must have interactive/active styling")
        for token in ("Receives", "Detects", "Writes / constrains", "Before next stage", "Failure looks like"):
            if token not in text[text.find("const SUBSTAGE_MAP"): text.find("function sourceFor")]:
                # These labels are emitted by the shared renderer, so require them near the renderer instead.
                renderer = text[text.find("function renderAuditTrace"): text.find("function attachStaticPipelineInteractivity")]
                if token not in renderer:
                    errors.append(f"architecture sub-card trace renderer missing {token}")
    standalone_pages = manifest.get("standalone_pages", []) if isinstance(manifest, dict) else []
    for page in standalone_pages:
        if not isinstance(page, dict):
            continue
        output = page.get("output")
        if isinstance(output, str):
            page_path = ROOT / output
            if not page_path.exists():
                errors.append(f"{output}: missing generated standalone page")
            else:
                page_text = page_path.read_text(encoding="utf-8")
                if GENERATED_BANNER not in page_text:
                    errors.append(f"{output}: missing generated-file banner")
                if "DOCS_PIPELINE_PROVENANCE" not in page_text:
                    errors.append(f"{output}: missing generated provenance block")
                if output == "docs/daee-epistemics-pipeline.html":
                    check_pipeline_notation_contract(page_text, output, errors)

    parser = IndexParser()
    parser.feed(text)

    seen_ids: dict[str, list[str]] = {}
    for tag, id_value in parser.ids:
        seen_ids.setdefault(id_value, []).append(tag)
    for id_value, tags in sorted(seen_ids.items()):
        if len(tags) > 1:
            errors.append(f"duplicate id {id_value!r} on tags {tags}")

    if not parser.tablist_seen:
        errors.append("missing top-level tablist role")

    tabs_by_label = {str(tab.get("label")): tab for tab in parser.tabs}
    panels_by_id = {str(panel.get("id")): panel for panel in parser.panels}

    for label, target in EXPECTED_TABS.items():
        tab = tabs_by_label.get(label)
        if not tab:
            errors.append(f"missing top-level tab {label!r}")
            continue
        if tab.get("data-tab") != target:
            errors.append(f"{label}: data-tab should be {target!r}")
        if tab.get("aria-controls") != target:
            errors.append(f"{label}: aria-controls should be {target!r}")
        if tab.get("role") != "tab":
            errors.append(f"{label}: missing role='tab'")
        if target not in panels_by_id:
            errors.append(f"{label}: target panel {target!r} missing")
            continue
        panel = panels_by_id[target]
        if panel.get("role") != "tabpanel":
            errors.append(f"{target}: missing role='tabpanel'")
        if panel.get("aria-labelledby") != tab.get("id"):
            errors.append(f"{target}: aria-labelledby does not point back to tab id")

    expected_targets = set(EXPECTED_TABS.values())
    actual_targets = {str(tab.get("data-tab")) for tab in parser.tabs}
    actual_panels = set(panels_by_id)
    extra_panels = actual_panels - expected_targets
    extra_targets = actual_targets - expected_targets
    missing_panels = expected_targets - actual_panels
    if extra_panels:
        errors.append(f"unexpected top-level tab panels: {sorted(extra_panels)}")
    if extra_targets:
        errors.append(f"unexpected top-level tab targets: {sorted(extra_targets)}")
    if missing_panels:
        errors.append(f"missing top-level tab panels: {sorted(missing_panels)}")

    active_tabs = [tab for tab in parser.tabs if "active" in str(tab.get("class") or "").split()]
    active_panels = [panel for panel in parser.panels if "active" in str(panel.get("class") or "").split()]
    if len(active_tabs) != 1 or active_tabs[0].get("data-tab") != "architecture":
        errors.append("initial active tab must be Architecture only")
    if len(active_panels) != 1 or active_panels[0].get("id") != "architecture":
        errors.append("initial active panel must be architecture only")
    for panel in parser.panels:
        if panel.get("id") == "architecture" and panel.get("hidden"):
            errors.append("architecture panel must not be hidden initially")
        if panel.get("id") != "architecture" and not panel.get("hidden"):
            errors.append(f"{panel.get('id')}: inactive panel should be hidden initially")

    script = "\n".join(parser.scripts)
    required_script_tokens = [
        "function showTopTab",
        "function initTopTabs",
        "addEventListener('click'",
        "addEventListener('keydown'",
        "history.replaceState",
        "aria-selected",
        "hidden=!active",
    ]
    for token in required_script_tokens:
        if token not in script:
            errors.append(f"tab controller missing token {token!r}")
    for token in ("DOCS_INDEX_MODULE_CATALOGUE", "data-owner-source=\"atomics/skill/references/diagnostics/module-catalogue.json\""):
        if token not in script and token not in text:
            errors.append(f"generated owner/TTP table missing token {token!r}")
    if "renderOwnerSourceTable" not in script:
        errors.append("owner-derived module table provider renderOwnerSourceTable missing")

    check_notation_contract(text, errors)
    check_public_notation_surface(INDEX, text, errors)
    for source_path in (ARCHITECTURE_SECTION, THEORY_SECTION):
        if not source_path.exists():
            errors.append(f"{source_path.relative_to(ROOT).as_posix()}: missing docs index source section")
        else:
            check_public_notation_surface(source_path, source_path.read_text(encoding="utf-8"), errors)
    check_theory_control_cards(text, errors)

    expected = expected_modules(errors)
    embedded = embedded_modules(text, errors)
    if expected and embedded and expected != embedded:
        expected_ids = {item["id"] for item in expected}
        embedded_ids = {item["id"] for item in embedded}
        missing = sorted(expected_ids - embedded_ids)
        extra = sorted(embedded_ids - expected_ids)
        if missing:
            errors.append(f"generated index missing live module ids: {missing}")
        if extra:
            errors.append(f"generated index has stale module ids absent from catalogue: {extra}")
        drift = [
            module_id
            for module_id in sorted(expected_ids & embedded_ids)
            if next(item for item in expected if item["id"] == module_id)
            != next(item for item in embedded if item["id"] == module_id)
        ]
        if drift:
            errors.append(f"generated index module metadata drift: {drift[:20]}")

    run_generation_freshness_check(errors)

    run_node_syntax_check(parser.scripts, errors)

    if errors:
        print("docs/index.html interaction check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("docs/index.html interaction check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
