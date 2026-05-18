"""Check docs/index.html top-level tab interaction wiring.

This is a structural guard for the public control-wiki page. It catches the
regression class where visible tab buttons remain present but their target
panels, ARIA wiring, or JavaScript controller drift out of sync.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in underprovisioned envs
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    raise

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"
MANIFEST = ROOT / "docs" / "index" / "manifest.json"
DESIGN_MD = ROOT / "docs" / "index" / "DESIGN.md"
INDEX_TEMPLATE = ROOT / "docs" / "index" / "templates" / "index.html.tpl"
ARCHITECTURE_SECTION = ROOT / "docs" / "index" / "sections" / "architecture.html"
THEORY_SECTION = ROOT / "docs" / "index" / "sections" / "theory.html"
RUNTIME_ARCHITECTURE_SOURCE = ROOT / "docs" / "index" / "runtime-architecture.json"
MODULE_CATALOGUE = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "module-catalogue.json"
REFERENCE_ROOT = ROOT / "atomics" / "skill" / "references"
REFERENCE_SOURCE_PATHS = [
    ROOT / "atomics" / "skill" / "README.md",
    ROOT / "atomics" / "skill" / "SKILL.md",
]
GENERATED_BANNER = "GENERATED FILE: do not edit this HTML output directly"
ALLOWED_CLASSIFICATIONS = {
    "OWNER_DERIVED",
    "STRUCTURED_SOURCE_DERIVED",
    "CURATED_SUMMARY_WITH_OWNER_REFERENCES",
    "STATIC_SNAPSHOT",
    "LAYOUT_ONLY",
}

RUNTIME_CONTROL_JS_CLAIM_RE = re.compile(
    r"(?i)\b("
    r"runtime|control|noetic|burden|owner|TTP|operator|route|routing|IR|"
    r"Delta|Land|R\(H|closure|witness|source-status|package|smoke|release|"
    r"formalism|field diagnostics|LoopBreak"
    r")\b|[∇ΔΨ𝒞]",
)
LARGE_JS_CONSTANT_MIN_BYTES = 1200

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
    "Theory deltaB control card": 'data-theory-card="deltaB"',
    "Theory deltaK control card": 'data-theory-card="deltaK"',
    "Theory nabla-dot control card": 'data-theory-card="nablaDot"',
    "Theory nabla-cross control card": 'data-theory-card="nablaCross"',
    "Theory route-gradient control card": 'data-theory-card="gradient"',
    "Theory loop-break control card": 'data-theory-card="loopBreak"',
    "Theory PsiI control card": 'data-theory-card="PsiI"',
    "Theory coupling control card": 'data-theory-card="coupling"',
    "Theory nabla-dot notation token": "data-k=\"nablaDot\"",
    "Theory nabla-cross notation token": "data-k=\"nablaCross\"",
    "Theory route-gradient notation token": "data-k=\"gradient\"",
    "Theory loop-break notation token": "data-k=\"loopBreak\"",
    "Theory PsiI selector": 'data-theory-card="PsiI"',
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


def split_design_frontmatter(errors: list[str]) -> tuple[dict[str, object], str, str]:
    if not DESIGN_MD.exists():
        errors.append("docs/index/DESIGN.md missing")
        return {}, "", ""
    raw = DESIGN_MD.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        errors.append("docs/index/DESIGN.md must start with YAML front matter")
        return {}, "", raw
    try:
        _prefix, frontmatter, body = raw.split("---", 2)
    except ValueError:
        errors.append("docs/index/DESIGN.md missing closing front matter fence")
        return {}, "", raw
    try:
        parsed = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        errors.append(f"docs/index/DESIGN.md YAML parse error: {exc}")
        return {}, frontmatter, body
    if not isinstance(parsed, dict):
        errors.append("docs/index/DESIGN.md front matter must parse as a mapping")
        return {}, frontmatter, body
    return parsed, frontmatter, body


def css_token_name(raw: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", raw)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    return value.strip("-").lower()


def token_path_value(tokens: dict[str, object], path: str) -> object | None:
    value: object = tokens
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def walk_design_values(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            found.extend(walk_design_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk_design_values(child))
    elif isinstance(value, str):
        found.extend(re.findall(r"\{([^{}]+)\}", value))
    return found


def count_frontmatter_color_keys(frontmatter: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    in_colors = False
    for line in frontmatter.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            in_colors = line.startswith("colors:")
            continue
        if not in_colors:
            continue
        match = re.match(r"^  ([A-Za-z0-9_-]+):", line)
        if match:
            key = match.group(1)
            counts[key] = counts.get(key, 0) + 1
    return counts


def hex_luminance(value: str) -> float | None:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return None
    channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]

    def channel_lum(channel: float) -> float:
        return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel_lum(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float | None:
    fg = hex_luminance(foreground)
    bg = hex_luminance(background)
    if fg is None or bg is None:
        return None
    lighter = max(fg, bg)
    darker = min(fg, bg)
    return (lighter + 0.05) / (darker + 0.05)


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
    derived_data = manifest.get("derived_data") or {}
    if not isinstance(derived_data, dict) or derived_data.get("runtime_architecture") != "docs/index/runtime-architecture.json":
        errors.append("manifest derived_data.runtime_architecture must point to docs/index/runtime-architecture.json")
    if not isinstance(derived_data, dict) or derived_data.get("design_system") != "docs/index/DESIGN.md":
        errors.append("manifest derived_data.design_system must point to docs/index/DESIGN.md")
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
        if tab.get("id") in {"architecture", "theory"}:
            generated_sources = {
                block.get("owner_source")
                for block in (tab.get("generated_blocks") or [])
                if isinstance(block, dict)
            }
            if "docs/index/runtime-architecture.json" not in generated_sources:
                errors.append(f"manifest tab {tab.get('id')!r} must generate its runtime architecture blocks from docs/index/runtime-architecture.json")
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


def check_docs_index_design_system(text: str, manifest: dict[str, object], errors: list[str]) -> None:
    design, frontmatter, body = split_design_frontmatter(errors)
    if not design:
        return

    required_groups = ("colors", "typography", "spacing", "radius", "rounded", "shadow", "motion", "components")
    for group in required_groups:
        if not isinstance(design.get(group), dict) or not design[group]:
            errors.append(f"docs/index/DESIGN.md missing required token group {group}")

    colors = design.get("colors")
    if not isinstance(colors, dict):
        return
    required_stage_colors = [
        "stageD0",
        "stagePsiN",
        "stageDslIr",
        "stageOwnerTtpDelta",
        "stageCollapseRestoration",
    ]
    color_counts = count_frontmatter_color_keys(frontmatter)
    for key in required_stage_colors:
        if key not in colors:
            errors.append(f"docs/index/DESIGN.md missing required stage color {key}")
        elif color_counts.get(key, 0) != 1:
            errors.append(f"docs/index/DESIGN.md stage color {key} must appear exactly once")
        elif not isinstance(colors[key], str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(colors[key])):
            errors.append(f"docs/index/DESIGN.md stage color {key} must be #RRGGBB")

    for ref in walk_design_values(design):
        if token_path_value(design, ref) is None:
            errors.append(f"docs/index/DESIGN.md token reference {{{ref}}} does not resolve")

    needed_sections = [
        "## Overview",
        "## Visual principles",
        "## Color semantics",
        "## Stage color rules",
        "## Typography and notation",
        "## Spacing and density",
        "## Carousel behavior",
        "## Accessibility and contrast",
        "## Do / Do not",
        "## Source ownership",
    ]
    for heading in needed_sections:
        if heading not in body:
            errors.append(f"docs/index/DESIGN.md missing rationale section {heading}")

    if "docs-index-design-source: docs/index/DESIGN.md" not in text:
        errors.append("generated docs/index.html missing DESIGN.md source marker in CSS")
    generated_vars = [
        "--ds-color-background",
        "--ds-color-stage-d0",
        "--ds-color-stage-psi-n",
        "--ds-color-stage-dsl-ir",
        "--ds-color-stage-owner-ttp-delta",
        "--ds-color-stage-collapse-restoration",
        "--ds-font-body",
        "--ds-space-carousel-gap",
        "--ds-radius-card",
        "--ds-shadow-active-card",
        "--ds-motion-duration",
        "--ds-carousel-primary-width",
        "--ds-carousel-preview-source-width",
        "--ds-carousel-preview-near-scale",
        "--ds-carousel-preview-far-scale",
        "--ds-carousel-preview-near-slot-height",
        "--stage-d0",
        "--stage-collapse-restoration-rgb",
    ]
    for token in generated_vars:
        if token not in text:
            errors.append(f"generated docs/index.html missing design CSS custom property {token}")

    template = INDEX_TEMPLATE.read_text(encoding="utf-8") if INDEX_TEMPLATE.exists() else ""
    for token in (
        "{{ DESIGN_TOKENS_CSS }}",
        "--v61-carousel-primary:var(--ds-carousel-primary-width)",
        "--v61-carousel-side:var(--ds-carousel-side-width)",
        "--v61-carousel-far:var(--ds-carousel-far-width)",
        "--v61-carousel-gap:var(--ds-carousel-gap)",
        "scale(var(--ds-carousel-preview-near-scale))",
        "scale(var(--ds-carousel-preview-far-scale))",
        "var(--ds-motion-duration)",
        "var(--ds-color-focus)",
    ):
        if token not in template:
            errors.append(f"docs/index template must reference design token surface {token}")

    architecture_css_start = text.find("#architecture #canonical-architecture-runtime .v56-input")
    architecture_css_end = text.find("/* v61: Architecture cards", architecture_css_start)
    architecture_css = text[architecture_css_start:architecture_css_end] if architecture_css_start != -1 else ""
    if architecture_css_start == -1:
        errors.append("architecture CSS block missing for design-token stage-color check")
    else:
        stale_stage_rgba = [
            "rgba(96,165,250",
            "rgba(34,211,238",
            "rgba(167,139,250",
            "rgba(251,146,60",
            "rgba(248,113,113",
        ]
        for stale in stale_stage_rgba:
            if stale in architecture_css:
                errors.append(f"architecture stage CSS still hardcodes stale stage color {stale}; use DESIGN.md tokens")

    visible_blocks = manifest.get("visible_blocks") if isinstance(manifest, dict) else []
    design_block = next(
        (
            block
            for block in visible_blocks or []
            if isinstance(block, dict) and block.get("id") == "docs_index_design_system"
        ),
        None,
    )
    if not design_block or design_block.get("current_source") != "docs/index/DESIGN.md":
        errors.append("manifest must mark docs/index/DESIGN.md as the docs/index design source")

    if ":focus-visible" not in text or "--ds-color-focus" not in text:
        errors.append("docs/index generated CSS must include token-backed focus-visible styles")
    if "@media(prefers-reduced-motion:reduce)" not in text:
        errors.append("docs/index generated CSS must preserve reduced-motion handling")
    if "setInterval(" in text:
        errors.append("docs/index carousel must not use automatic rotation timers")

    contrast_pairs = [
        ("colors.text", "colors.background"),
        ("colors.textSubtle", "colors.surface"),
        ("colors.textMuted", "colors.background"),
        ("colors.text", "colors.surfaceCode"),
    ]
    for foreground_path, background_path in contrast_pairs:
        foreground = token_path_value(design, foreground_path)
        background = token_path_value(design, background_path)
        if not isinstance(foreground, str) or not isinstance(background, str):
            errors.append(f"contrast token pair missing {foreground_path}/{background_path}")
            continue
        ratio = contrast_ratio(foreground, background)
        if ratio is None or ratio < 4.5:
            detail = f"{ratio:.2f}:1" if ratio is not None else "unparseable color"
            errors.append(f"contrast sanity check failed for {foreground_path} on {background_path}: {detail}")


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


def expected_reference_paths() -> list[Path]:
    paths = [path for path in REFERENCE_SOURCE_PATHS if path.exists()]
    paths.extend(sorted(REFERENCE_ROOT.rglob("*.md")))
    seen: dict[Path, Path] = {}
    for path in paths:
        seen[path.resolve()] = path
    return [seen[key] for key in sorted(seen, key=lambda item: str(item))]


def extract_js_array(text: str, name: str, errors: list[str]) -> list[object]:
    marker = f"const {name} = "
    marker_start = text.find(marker)
    if marker_start == -1:
        errors.append(f"generated reference data missing const {name}")
        return []
    start = text.find("[", marker_start + len(marker))
    if start == -1:
        errors.append(f"generated reference data const {name} is not an array")
        return []
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                raw = text[start : index + 1]
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    errors.append(f"generated reference data const {name} is invalid JSON: {exc}")
                    return []
                if not isinstance(payload, list):
                    errors.append(f"generated reference data const {name} must be a list")
                    return []
                return payload
    errors.append(f"generated reference data const {name} array is unterminated")
    return []


def strip_js_array_const(text: str, name: str) -> str:
    marker = f"const {name} = "
    marker_start = text.find(marker)
    if marker_start == -1:
        return text
    start = text.find("[", marker_start + len(marker))
    if start == -1:
        return text
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index + 1
                if end < len(text) and text[end] == ";":
                    end += 1
                return text[:marker_start] + f"const {name} = [];" + text[end:]
    return text


def strip_reference_snapshots(text: str) -> str:
    # DOCS embeds source-owned markdown snapshots. Public-surface claim checks
    # must inspect the visible index rendering, not every quoted owner source.
    return strip_js_array_const(strip_js_array_const(text, "REFS"), "DOCS")


def extract_js_object_block(text: str, name: str, errors: list[str]) -> str:
    marker = f"const {name} = "
    marker_start = text.find(marker)
    if marker_start == -1:
        errors.append(f"generated trace data missing const {name}")
        return ""
    start = text.find("{", marker_start + len(marker))
    if start == -1:
        errors.append(f"generated trace data const {name} is not an object")
        return ""
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    errors.append(f"generated trace data const {name} object is unterminated")
    return ""


def has_js_object_key(block: str, key: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_$-])(?:['\"]{re.escape(key)}['\"]|{re.escape(key)})\s*:",
        block,
    ) is not None


def plain_html(value: object) -> str:
    return re.sub(r"<[^>]+>", "", str(value)).strip()


def load_runtime_architecture_for_check(errors: list[str]) -> dict[str, object]:
    if not RUNTIME_ARCHITECTURE_SOURCE.exists():
        errors.append("docs/index/runtime-architecture.json missing; Architecture trace maps need a shared source")
        return {}
    try:
        payload = json.loads(RUNTIME_ARCHITECTURE_SOURCE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"docs/index/runtime-architecture.json JSON parse error: {exc}")
        return {}
    if payload.get("schema_version") != 1:
        errors.append("docs/index/runtime-architecture.json schema_version must be 1")
    if payload.get("status") != "shared-runtime-architecture-source":
        errors.append("docs/index/runtime-architecture.json status must be shared-runtime-architecture-source")
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("docs/index/runtime-architecture.json must define non-empty stages")
    return payload


def runtime_stage_title(stage: dict[str, object]) -> str:
    title = stage.get("title")
    if isinstance(title, str) and title:
        return title
    return plain_html(stage.get("title_html", ""))


def check_architecture_trace_parity(text: str, errors: list[str]) -> None:
    arch = load_runtime_architecture_for_check(errors)
    stages = arch.get("stages")
    if not isinstance(stages, list) or not stages:
        return

    static_map = extract_js_object_block(text, "STATIC_STAGE_MAP", errors)
    substage_map = extract_js_object_block(text, "SUBSTAGE_MAP", errors)
    js_stages = extract_js_array(text, "ARCHITECTURE_STAGES", errors)
    parity_marker = (
        "Architecture interaction trace maps are parity-checked against "
        "docs/index/runtime-architecture.json"
    )
    if parity_marker not in text:
        errors.append("architecture trace maps missing source/parity marker comment")

    if len(js_stages) != len(stages):
        errors.append(f"ARCHITECTURE_STAGES count drift: expected {len(stages)}, found {len(js_stages)}")
    for index, stage_obj in enumerate(stages):
        if not isinstance(stage_obj, dict):
            errors.append(f"runtime architecture stage {index} is malformed")
            continue
        key = str(stage_obj.get("key", ""))
        title = runtime_stage_title(stage_obj)
        number = str(stage_obj.get("number", ""))
        if not key:
            errors.append(f"runtime architecture stage {index} missing key")
            continue
        if f'data-stage-key="{key}"' not in text:
            errors.append(f"generated Architecture cards missing data-stage-key={key!r}")
        if static_map and not has_js_object_key(static_map, key):
            errors.append(f"STATIC_STAGE_MAP.target missing shared stage key {key!r}")
        if substage_map and not has_js_object_key(substage_map, key):
            errors.append(f"SUBSTAGE_MAP.target missing shared stage key {key!r}")
        if title and static_map and title not in static_map:
            errors.append(f"STATIC_STAGE_MAP target stage {key!r} title drifts from shared source: {title!r}")
        if index < len(js_stages) and isinstance(js_stages[index], dict):
            js_title = plain_html(js_stages[index].get("title", ""))
            js_number = str(js_stages[index].get("n", ""))
            if title and js_title != title:
                errors.append(
                    f"ARCHITECTURE_STAGES[{index}] title drift: expected {title!r}, found {js_title!r}"
                )
            if number and js_number != number:
                errors.append(
                    f"ARCHITECTURE_STAGES[{index}] stage number drift: expected {number!r}, found {js_number!r}"
                )
        subcards = stage_obj.get("subcards")
        if not isinstance(subcards, list):
            errors.append(f"runtime architecture stage {key!r} must define subcards")
            continue
        for card in subcards:
            if not isinstance(card, dict):
                errors.append(f"runtime architecture stage {key!r} has malformed subcard")
                continue
            subkey = str(card.get("key", ""))
            card_title = str(card.get("title", ""))
            if not subkey:
                errors.append(f"runtime architecture stage {key!r} has subcard without key")
                continue
            if f'data-substage-key="{subkey}"' not in text:
                errors.append(f"generated Architecture cards missing data-substage-key={subkey!r}")
            if substage_map and not has_js_object_key(substage_map, subkey):
                errors.append(f"SUBSTAGE_MAP.target.{key} missing shared subcard key {subkey!r}")
            if card_title and substage_map and card_title not in substage_map:
                errors.append(
                    f"SUBSTAGE_MAP target subcard {key}.{subkey} title drifts from shared source: {card_title!r}"
                )


def tab_section_slice(text: str, section_id: str) -> str:
    match = re.search(rf'<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>', text)
    if not match:
        return ""
    next_match = re.search(r'\n<section\b[^>]*\bclass="tabsec', text[match.end() :])
    if not next_match:
        return text[match.start() :]
    return text[match.start() : match.end() + next_match.start()]


def div_slice_for_marker(text: str, marker: str) -> str:
    start = text.find(marker)
    if start == -1:
        return ""
    end = text.find("</div>", start)
    if end == -1:
        return text[start:]
    return text[start : end + len("</div>")]


def normalized_render_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip().lower()


def mapping_row_values(row: object) -> tuple[str, str, str] | None:
    if isinstance(row, dict):
        notation = row.get("notation")
        role = row.get("runtime_role") or row.get("role")
        owner = row.get("source_owner") or row.get("owner")
        if all(isinstance(value, str) for value in (notation, role, owner)):
            return str(notation), str(role), str(owner)
        return None
    if isinstance(row, list) and len(row) >= 3 and all(isinstance(value, str) for value in row[:3]):
        return str(row[0]), str(row[1]), str(row[2])
    return None


def require_ordered_tokens(block: str, tokens: list[str], label: str, errors: list[str]) -> None:
    cursor = 0
    for token in tokens:
        rendered = html.escape(token, quote=True)
        found = block.find(rendered, cursor)
        if found == -1:
            errors.append(f"{label} missing shared runtime token {token!r}")
            continue
        cursor = found + len(rendered)


def check_shared_runtime_renderings(text: str, errors: list[str]) -> None:
    """Guard the three related renderings of the same runtime sequence.

    The Architecture tab intentionally has two rows, and Theory has a related
    notation/mapping rendering. This check prevents collapsing them or letting
    any of the three drift away from docs/index/runtime-architecture.json.
    """

    arch = load_runtime_architecture_for_check(errors)
    rows = arch.get("rows")
    mapping_rows = arch.get("mapping_rows")
    notation_lines = arch.get("notation_lines")
    if not isinstance(rows, dict) or not isinstance(mapping_rows, list):
        errors.append("docs/index/runtime-architecture.json must define rows and mapping_rows for shared rendering checks")
        return

    architecture = tab_section_slice(text, "architecture")
    theory = tab_section_slice(text, "theory")
    if not architecture:
        errors.append("Architecture tab section missing for shared runtime rendering check")
        return
    if not theory:
        errors.append("Theory tab section missing for shared runtime rendering check")
        return

    plain_row = div_slice_for_marker(architecture, 'data-runtime-rendering="architecture-plain-row"')
    formal_row = div_slice_for_marker(architecture, 'data-runtime-rendering="architecture-formal-row"')
    if not plain_row:
        errors.append("Architecture plain runtime row missing data-runtime-rendering marker")
    if not formal_row:
        errors.append("Architecture formal runtime row missing data-runtime-rendering marker")

    runtime_items = rows.get("runtime")
    formal_items = rows.get("formal")
    if isinstance(runtime_items, list) and plain_row:
        runtime_labels = [str(item.get("label", "")) for item in runtime_items if isinstance(item, dict)]
        require_ordered_tokens(plain_row, runtime_labels, "Architecture plain row", errors)
    else:
        errors.append("docs/index/runtime-architecture.json rows.runtime must be a list")
        runtime_labels = []
    if isinstance(formal_items, list) and formal_row:
        formal_labels = [str(item.get("label", "")) for item in formal_items if isinstance(item, dict)]
        require_ordered_tokens(formal_row, formal_labels, "Architecture formal row", errors)
    else:
        errors.append("docs/index/runtime-architecture.json rows.formal must be a list")
        formal_labels = []

    if 'data-runtime-rendering="architecture-plain-row"' in theory:
        errors.append("Architecture plain row must remain on Architecture tab, not Theory")
    if 'data-runtime-rendering="architecture-formal-row"' in theory:
        errors.append("Architecture formal row must remain on Architecture tab, not Theory")
    if 'data-runtime-rendering="theory-formalism-notation"' not in theory:
        errors.append("Theory formalism notation rendering missing shared-source marker")
    if 'data-runtime-rendering="theory-formalism-mapping"' not in theory:
        errors.append("Theory formalism mapping rendering missing shared-source marker")

    parsed_mapping_rows = [values for values in (mapping_row_values(row) for row in mapping_rows) if values]
    if len(parsed_mapping_rows) != len(mapping_rows):
        errors.append("docs/index/runtime-architecture.json mapping_rows contains malformed rows")
    for notation, role, owner in parsed_mapping_rows:
        require_ordered_tokens(theory, [notation, role, owner], "Theory shared mapping", errors)

    if isinstance(notation_lines, list):
        notation_tokens = [
            str(segment.get("token"))
            for line in notation_lines
            if isinstance(line, list)
            for segment in line
            if isinstance(segment, dict) and isinstance(segment.get("token"), str)
        ]
        for token in sorted(set(notation_tokens)):
            if f'data-k="{html.escape(token, quote=True)}"' not in theory:
                errors.append(f"Theory notation rendering missing shared notation token {token!r}")

    plain_normal = normalized_render_text(" ".join(runtime_labels))
    formal_normal = normalized_render_text(" ".join(formal_labels))
    theory_normal = normalized_render_text(" ".join(row[0] for row in parsed_mapping_rows))
    if plain_normal and plain_normal == formal_normal:
        errors.append("Architecture plain and formal rows must remain related but not text-identical")
    if theory_normal and theory_normal in {plain_normal, formal_normal}:
        errors.append("Theory formalism rendering must map the same sequence without duplicating an Architecture row")


def check_architecture_carousel_contract(text: str, errors: list[str]) -> None:
    """Verify the Architecture cards render as a selected-primary carousel.

    The carousel is presentation only. Runtime stage identity still comes from
    docs/index/runtime-architecture.json, and the Architecture rows / Theory
    rendering remain separate shared-source surfaces.
    """

    arch = load_runtime_architecture_for_check(errors)
    stages = arch.get("stages")
    if not isinstance(stages, list) or not stages:
        return

    architecture = tab_section_slice(text, "architecture")
    if not architecture:
        errors.append("Architecture tab section missing for carousel contract check")
        return

    start = architecture.find('data-carousel="architecture-runtime"')
    if start == -1:
        errors.append("Architecture runtime carousel container missing data-carousel marker")
        return
    end = architecture.find('id="targetStaticStageDetail"', start)
    carousel = architecture[start:] if end == -1 else architecture[start:end]

    expected_keys = [str(stage.get("key", "")) for stage in stages if isinstance(stage, dict)]
    found_cards = re.findall(r"<article\b[^>]*\bv60-carousel-card\b[^>]*>", carousel)
    found_slots = re.findall(r"<div\b[^>]*\bv60-carousel-slot\b[^>]*>", carousel)
    card_slices = [
        carousel[match.start() : carousel.find("</article>", match.end()) + len("</article>")]
        for match in re.finditer(r"<article\b[^>]*\bv60-carousel-card\b[^>]*>", carousel)
        if carousel.find("</article>", match.end()) != -1
    ]
    if len(found_cards) != len(expected_keys):
        errors.append(f"Architecture carousel should render {len(expected_keys)} stage cards, found {len(found_cards)}")
    if len(found_slots) != len(expected_keys):
        errors.append(f"Architecture carousel should wrap each generated card in a scaled preview slot, found {len(found_slots)} slots")
    if len(card_slices) != len(found_cards):
        errors.append("Architecture carousel card markup is malformed; every stage card must close as an article")
    for index, key in enumerate(expected_keys):
        if f'data-stage-key="{html.escape(key, quote=True)}"' not in carousel:
            errors.append(f"Architecture carousel missing stage card for shared key {key!r}")
        if f'data-carousel-index="{index}"' not in carousel:
            errors.append(f"Architecture carousel missing stable data-carousel-index={index}")

    active_cards = [
        card
        for card in found_cards
        if re.search(r'\bclass="[^"]*\bv30-active\b', card)
    ]
    selected_cards = [card for card in found_cards if 'aria-selected="true"' in card]
    if len(active_cards) != 1:
        errors.append(f"Architecture carousel must have exactly one default active primary card, found {len(active_cards)}")
    if len(selected_cards) != 1:
        errors.append(f"Architecture carousel must have exactly one default aria-selected card, found {len(selected_cards)}")
    if expected_keys and selected_cards and f'data-stage-key="{expected_keys[0]}"' not in selected_cards[0]:
        errors.append("Architecture carousel default selected card should be the first shared runtime stage")
    preview_cards = [card for card in found_cards if 'aria-selected="false"' in card]
    if len(preview_cards) != max(0, len(expected_keys) - 1):
        errors.append("Architecture carousel must mark every non-primary stage as a preview/selectable card")
    for card in preview_cards:
        if "is-preview" not in card:
            errors.append("Architecture carousel preview card missing is-preview class")
    for slot in found_slots:
        if 'data-carousel-position="center"' not in slot and "is-preview" not in slot:
            errors.append("Architecture carousel preview slot missing is-preview class")
    for index, card_markup in enumerate(card_slices):
        if "v21-stage" not in found_cards[index] or "v30-selectable-stage" not in found_cards[index]:
            errors.append("Architecture carousel cards must reuse the generated stage card class family")
        if "v60-selectable-subcard" not in card_markup or "data-substage-key=" not in card_markup:
            errors.append("Architecture carousel cards must include generated subcard content, not title-only preview markup")
    hidden_preview_subcards = re.search(
        r"\.v60-carousel-card\s+\.v60-selectable-subcard\s*\{[^}]*display\s*:\s*none",
        text,
        flags=re.S,
    )
    if hidden_preview_subcards:
        errors.append("Architecture carousel preview cards must not hide generated subcards into title-only tiles")
    required_preview_css = [
        ".v60-carousel-slot:not([data-carousel-position=\"center\"])",
        "scale(var(--ds-carousel-preview-near-scale))",
        "scale(var(--ds-carousel-preview-far-scale))",
        "width:var(--ds-carousel-preview-source-width)",
        "overflow:visible!important",
    ]
    for token in required_preview_css:
        if token not in text:
            errors.append(f"Architecture carousel scaled-preview CSS missing {token!r}")
    if re.search(
        r"\.v60-carousel-slot:not\(\[data-carousel-position=\"center\"\]\)\s*>\s*\.v60-carousel-card\s*\{[^}]*overflow\s*:\s*hidden",
        text,
        flags=re.S,
    ):
        errors.append("Architecture carousel preview cards must scale inside slots, not crop with overflow hidden")
    dense_layout_tokens = [
        "v60-example-group",
        "v60-field-chiprow",
        "v60-loopbreak-formula",
        "v60-grounding-block",
        'data-decision-layout="2x2-plus-complete"',
        ".v62-decision-grid .complete",
    ]
    for token in dense_layout_tokens:
        if token not in text:
            errors.append(f"Architecture card 4 containment/layout token missing {token!r}")

    for action in ("prev", "next"):
        if f'data-carousel-action="{action}"' not in carousel:
            errors.append(f"Architecture carousel missing {action!r} control")
    if 'class="v60-carousel-dot"' not in carousel:
        errors.append("Architecture carousel missing selectable stage dot buttons")
    if "architectureCarouselStatus" not in carousel:
        errors.append("Architecture carousel missing aria-live selected-stage status")
    if "ArrowRight" not in text or "ArrowLeft" not in text:
        errors.append("Architecture carousel missing keyboard arrow navigation")
    if "setInterval(" in text or "requestAnimationFrame(" in text or "auto-rotate" in text.lower():
        errors.append("Architecture carousel must remain user-controlled with no auto-rotation timer")
    if "prefers-reduced-motion:reduce" not in text:
        errors.append("Architecture carousel missing prefers-reduced-motion handling")
    if "<noscript><style>" not in carousel or "v60-architecture-rail" not in carousel:
        errors.append("Architecture carousel missing no-JS fallback style")
    if "@media print" not in text or "v60-carousel-controls" not in text:
        errors.append("Architecture carousel missing print fallback for all cards")


def operator_reference_paths() -> set[str]:
    paths = {path.relative_to(ROOT).as_posix() for path in REFERENCE_ROOT.rglob("*.md")}
    paths.update(path.relative_to(ROOT).as_posix() for path in REFERENCE_SOURCE_PATHS if path.exists())
    return paths


def owner_token_resolves(token: str, operators: list[dict[str, object]], source_paths: set[str]) -> bool:
    value = token.strip()
    if not value:
        return True
    op_ids = {str(op.get("id", "")) for op in operators}
    aliases = {
        str(alias)
        for op in operators
        for alias in (op.get("aliases") or [])
        if isinstance(alias, str)
    }
    stems = {Path(path).stem for path in source_paths}
    names = {Path(path).name for path in source_paths}
    if value in op_ids or value in aliases or value in stems or value in names:
        return True
    if value.endswith(".md") and value in names:
        return True
    range_match = re.fullmatch(r"([A-Z]+)(\d+)-(?:[A-Z]+)?(\d+)", value)
    if range_match:
        prefix, start, end = range_match.groups()
        start_i = int(start)
        end_i = int(end)
        if start_i > end_i:
            return False
        for number in range(start_i, end_i + 1):
            candidate = f"{prefix}{number}"
            if candidate not in aliases and not any(op_id == candidate or op_id.startswith(f"{candidate}-") for op_id in op_ids):
                return False
        return True
    return False


def check_owner_ttp_map_parity(text: str, expected: list[dict[str, str]], errors: list[str]) -> None:
    operators_raw = extract_js_array(text, "OPERATORS", errors)
    families_raw = extract_js_array(text, "OWNER_FAMILIES", errors)
    if not operators_raw or not families_raw:
        return
    operators = [op for op in operators_raw if isinstance(op, dict)]
    families = [family for family in families_raw if isinstance(family, dict)]
    if len(operators) != len(operators_raw):
        errors.append("OPERATORS contains malformed non-object entries")
    if len(families) != len(families_raw):
        errors.append("OWNER_FAMILIES contains malformed non-object entries")

    parity_marker = (
        "Owner/TTP operator and family maps are parity-checked against "
        "module-catalogue/frontmatter/source paths"
    )
    if parity_marker not in text:
        errors.append("Owner/TTP maps missing source/parity marker comment")

    expected_by_id = {module["id"]: module for module in expected}
    expected_by_source = {module["source_path"]: module for module in expected}
    source_paths = operator_reference_paths()
    seen_operator_ids: set[str] = set()
    operator_families: set[str] = set()
    required_fields = ("id", "family", "class", "label", "activation", "operation", "delta", "reread", "path")
    for op in operators:
        op_id = str(op.get("id", ""))
        if not op_id:
            errors.append("OPERATORS entry missing id")
            continue
        if op_id in seen_operator_ids:
            errors.append(f"OPERATORS duplicate id {op_id!r}")
        seen_operator_ids.add(op_id)
        for field in required_fields:
            if not isinstance(op.get(field), str) or not str(op.get(field)).strip():
                errors.append(f"OPERATORS[{op_id}] missing required field {field!r}")
        family = str(op.get("family", ""))
        if family:
            operator_families.add(family)
        path = str(op.get("path", ""))
        if path and path not in source_paths:
            errors.append(f"OPERATORS[{op_id}] path is not a tracked atomics/reference source: {path}")
        catalogue_entry = expected_by_id.get(op_id) or expected_by_source.get(path)
        if catalogue_entry:
            if path and path != catalogue_entry["source_path"]:
                errors.append(
                    f"OPERATORS[{op_id}] source path drift: expected {catalogue_entry['source_path']}, found {path}"
                )
            if str(op.get("class", "")) != catalogue_entry["module_class"]:
                errors.append(
                    f"OPERATORS[{op_id}] class drift: expected {catalogue_entry['module_class']}, found {op.get('class')!r}"
                )
        elif path:
            aliases = op.get("aliases") or []
            if op_id not in Path(path).stem and op_id not in aliases:
                # Non-catalogue operators are allowed only when clearly source-linked
                # through their file identity or an explicit alias.
                errors.append(f"OPERATORS[{op_id}] is not catalogue-backed and lacks a file-stem/alias source link")

    option_families = set(re.findall(r"<option>([^<]+)</option>", text))
    missing_options = sorted(operator_families - option_families)
    if missing_options:
        errors.append(f"Owner/TTP operator family filter missing options: {missing_options}")

    for family in families:
        family_id = str(family.get("id", ""))
        owners = family.get("owners")
        if not family_id:
            errors.append("OWNER_FAMILIES entry missing id")
        if not isinstance(owners, list) or not owners:
            errors.append(f"OWNER_FAMILIES[{family_id}] must list source owners")
            continue
        unresolved = [
            str(owner)
            for owner in owners
            if isinstance(owner, str) and not owner_token_resolves(owner, operators, source_paths)
        ]
        if unresolved:
            errors.append(f"OWNER_FAMILIES[{family_id}] has unresolved owner/source tokens: {unresolved}")

    if re.search(r"\b69\s+modules?\b", strip_reference_snapshots(text), flags=re.I):
        errors.append("docs/index public surface must not hardcode a literal '69 modules' claim")


def check_reference_data(text: str, errors: list[str]) -> None:
    if "const PROCEDURE" in text:
        errors.append("docs/index.html still embeds stale PROCEDURE release-status data")
    if "auditSummary" in text:
        errors.append("docs/index.html still embeds stale auditSummary release-status text")
    refs = extract_js_array(text, "REFS", errors)
    docs = extract_js_array(text, "DOCS", errors)
    expected_paths = [path.relative_to(ROOT).as_posix() for path in expected_reference_paths()]
    ref_paths = [entry.get("path") for entry in refs if isinstance(entry, dict)]
    doc_paths = [entry.get("rel") for entry in docs if isinstance(entry, dict)]
    if ref_paths and ref_paths != expected_paths:
        errors.append("generated REFS paths drift from atomics/skill README, SKILL.md, and references/**/*.md")
    if doc_paths and doc_paths != expected_paths:
        errors.append("generated DOCS paths drift from atomics/skill README, SKILL.md, and references/**/*.md")
    docs_by_path = {entry.get("rel"): entry for entry in docs if isinstance(entry, dict)}
    refs_by_path = {entry.get("path"): entry for entry in refs if isinstance(entry, dict)}
    for path in expected_reference_paths():
        rel_path = path.relative_to(ROOT).as_posix()
        text_current = path.read_text(encoding="utf-8")
        doc = docs_by_path.get(rel_path)
        ref = refs_by_path.get(rel_path)
        if not isinstance(doc, dict):
            errors.append(f"generated DOCS missing source snapshot for {rel_path}")
            continue
        if doc.get("content") != text_current:
            errors.append(f"generated DOCS source snapshot drift: {rel_path}")
        if doc.get("lines") != len(text_current.splitlines()):
            errors.append(f"generated DOCS line count drift: {rel_path}")
        if isinstance(ref, dict) and ref.get("lines") != len(text_current.splitlines()):
            errors.append(f"generated REFS line count drift: {rel_path}")


def manifest_js_constant_coverage(manifest: dict[str, object]) -> set[str]:
    covered: set[str] = set()

    def collect(entry: object) -> None:
        if not isinstance(entry, dict):
            return
        constants = entry.get("js_constants")
        if isinstance(constants, list):
            covered.update(str(value) for value in constants if isinstance(value, str) and value)
        for block in entry.get("generated_blocks", []) or []:
            collect(block)

    for tab in manifest.get("tabs", []) or []:
        collect(tab)
    for block in manifest.get("visible_blocks", []) or []:
        collect(block)
    for page in manifest.get("standalone_pages", []) or []:
        collect(page)
    return covered


def iter_const_blocks(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for match in re.finditer(r"(?m)^\s*const\s+([A-Z][A-Z0-9_]*)\s*=", text):
        name = match.group(1)
        end = text.find(";\n", match.end())
        if end == -1:
            line_end = text.find("\n", match.end())
            end = len(text) if line_end == -1 else line_end
        else:
            end += 1
        found.append((name, text[match.start() : end]))
    return found


def check_large_runtime_control_js_inventory(text: str, manifest: dict[str, object], errors: list[str]) -> None:
    covered = manifest_js_constant_coverage(manifest)
    const_blocks = iter_const_blocks(text)
    present_names = {name for name, _block in const_blocks}
    for name, block in const_blocks:
        if len(block.encode("utf-8")) < LARGE_JS_CONSTANT_MIN_BYTES:
            continue
        if not RUNTIME_CONTROL_JS_CLAIM_RE.search(block):
            continue
        if name not in covered:
            errors.append(
                f"large runtime/control JS constant {name} lacks manifest js_constants coverage "
                "and checker/source-basis review"
            )
    for name in sorted(covered):
        if name not in present_names:
            errors.append(f"manifest js_constants entry {name} does not match a generated const declaration")


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
    card_tags = re.findall(r"<button\b(?=[^>]*\bcontrolCard\b)([^>]*)>", block)

    def attr(attrs: str, name: str) -> str:
        match = re.search(rf'\b{re.escape(name)}="([^"]*)"', attrs)
        return html.unescape(match.group(1)) if match else ""

    cards = [(attr(attrs, "class"), attr(attrs, "data-theory-card"), attrs) for attrs in card_tags]
    found = [concept for _classes, concept, _attrs in cards]
    if found != EXPECTED_CONTROL_CARD_ORDER:
        errors.append(
            "Theory control ontology cards must render in pipeline order: "
            f"expected {EXPECTED_CONTROL_CARD_ORDER!r}, found {found!r}"
        )

    arch = load_runtime_architecture_for_check(errors)
    theory_cards = arch.get("theory_cards")
    target_map = arch.get("theory_card_notation_targets")
    notation_lines = arch.get("notation_lines")
    source_card_ids: list[str] = []
    if isinstance(theory_cards, list):
        source_card_ids = [str(card.get("id")) for card in theory_cards if isinstance(card, dict)]
    if source_card_ids and found != source_card_ids:
        errors.append(
            "Theory control card order must derive from docs/index/runtime-architecture.json: "
            f"expected {source_card_ids!r}, found {found!r}"
        )
    if not isinstance(target_map, dict):
        errors.append("docs/index/runtime-architecture.json must define theory_card_notation_targets")
        target_map = {}

    notation_tokens: set[str] = set()
    if isinstance(notation_lines, list):
        for line in notation_lines:
            if not isinstance(line, list):
                continue
            for segment in line:
                if isinstance(segment, dict) and isinstance(segment.get("token"), str):
                    notation_tokens.add(segment["token"])
    if not notation_tokens:
        errors.append("docs/index/runtime-architecture.json must define source notation token ids")

    for css_class in REQUIRED_CONTROL_CARD_COLOR_CLASSES:
        if not re.search(rf"\.controlCard\.{re.escape(css_class)}\s*\{{[^}}]*--c\s*:", text, flags=re.S):
            errors.append(f"Theory control card class .controlCard.{css_class} must define --c color")

    class_by_concept = {concept: set(classes.split()) for classes, concept, _attrs in cards}
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

    pressed_cards = [concept for _classes, concept, attrs in cards if attr(attrs, "aria-pressed") == "true"]
    if len(pressed_cards) != 1:
        errors.append(f"Theory control cards must have exactly one deterministic default active card, found {pressed_cards!r}")
    elif pressed_cards[0] != EXPECTED_CONTROL_CARD_ORDER[0]:
        errors.append("Theory control cards should default to the first shared-source card")

    for _classes, concept, attrs in cards:
        if attr(attrs, "type") != "button":
            errors.append(f"Theory control card {concept!r} must be a real button control")
        if attr(attrs, "data-concept-id") != concept:
            errors.append(f"Theory control card {concept!r} missing stable data-concept-id")
        if "selectTheoryCard(this)" not in attr(attrs, "onclick"):
            errors.append(f"Theory control card {concept!r} must call selectTheoryCard(this), not only route to concept graph")
        targets = attr(attrs, "data-notation-targets").split()
        source_targets = target_map.get(concept)
        if not targets:
            errors.append(f"Theory control card {concept!r} missing data-notation-targets")
        if not isinstance(source_targets, list) or not source_targets:
            errors.append(f"runtime architecture source missing notation targets for theory card {concept!r}")
            source_targets = []
        if targets != source_targets:
            errors.append(
                f"Theory control card {concept!r} target drift: "
                f"generated {targets!r}, source {source_targets!r}"
            )
        for target in targets:
            if target not in notation_tokens:
                errors.append(f"Theory control card {concept!r} targets unknown source notation token {target!r}")
            if f'data-notation-id="{html.escape(target, quote=True)}"' not in text:
                errors.append(f"Theory control card {concept!r} target {target!r} has no generated notation chip")

    for token in sorted(notation_tokens):
        token_attr = f'data-notation-id="{html.escape(token, quote=True)}"'
        if token_attr not in text:
            errors.append(f"Theory notation token {token!r} missing generated data-notation-id")
        token_tag = re.search(rf"<span\b(?=[^>]*{re.escape(token_attr)})([^>]*)>", text)
        if not token_tag:
            continue
        attrs = token_tag.group(1)
        if attr(attrs, "role") != "button":
            errors.append(f"Theory notation token {token!r} must be keyboard-addressable role=button")
        if attr(attrs, "tabindex") != "0":
            errors.append(f"Theory notation token {token!r} must be focusable")
        if "highlightNotation(" not in attr(attrs, "onclick"):
            errors.append(f"Theory notation token {token!r} must retain highlightNotation click behavior")

    required_interaction_tokens = [
        "function selectTheoryCard",
        "function theoryCardTargetKeys",
        "function activateNotationToken",
        "is-linked-active",
        'aria-pressed="true"',
        ".controlCard.is-linked-active",
        ".ntok.is-linked-active",
    ]
    for token in required_interaction_tokens:
        if token not in text:
            errors.append(f"Theory card-to-notation interaction missing {token!r}")
    if "goConceptField('" in block:
        errors.append("Theory control cards must not depend on goConceptField-only concept routing")
    if "setInterval(" in text:
        errors.append("Theory card-to-notation interaction must not depend on automatic timers")

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
            ".v21-s1": "--sc:var(--stage-d0)",
            ".v21-s2": "--sc:var(--stage-psi-n)",
            ".v21-s3": "--sc:var(--stage-dsl-ir)",
            ".v21-s4": "--sc:var(--stage-owner-ttp-delta)",
            ".v21-s5": "--sc:var(--stage-collapse-restoration)",
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
        if ".v60-reread-phase" not in text or "--sc:var(--ds-color-success)" not in text[text.find(".v60-reread-phase"): text.find(".v60-reread-phase") + 220]:
            errors.append("architecture reread phase styling must use the design success phase token")
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
    check_reference_data(text, errors)

    public_text = strip_reference_snapshots(text)
    check_docs_index_design_system(text, manifest if isinstance(manifest, dict) else {}, errors)
    check_notation_contract(public_text, errors)
    check_public_notation_surface(INDEX, public_text, errors)
    check_architecture_trace_parity(text, errors)
    check_shared_runtime_renderings(text, errors)
    check_architecture_carousel_contract(text, errors)
    check_large_runtime_control_js_inventory(text, manifest if isinstance(manifest, dict) else {}, errors)
    runtime_source_text = ""
    if RUNTIME_ARCHITECTURE_SOURCE.exists():
        runtime_source_text = RUNTIME_ARCHITECTURE_SOURCE.read_text(encoding="utf-8")
    else:
        errors.append("docs/index/runtime-architecture.json missing; Architecture/Theory runtime renderings must share one source")
    for source_path in (ARCHITECTURE_SECTION, THEORY_SECTION):
        if not source_path.exists():
            errors.append(f"{source_path.relative_to(ROOT).as_posix()}: missing docs index source section")
        else:
            section_text = source_path.read_text(encoding="utf-8")
            if "docs/index/runtime-architecture.json" not in section_text:
                errors.append(f"{source_path.relative_to(ROOT).as_posix()}: must declare the shared runtime architecture source")
            check_public_notation_surface(source_path, f"{section_text}\n{runtime_source_text}", errors)
    check_theory_control_cards(text, errors)

    expected = expected_modules(errors)
    check_owner_ttp_map_parity(text, expected, errors)
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
