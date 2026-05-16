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


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"
MANIFEST = ROOT / "docs" / "index" / "manifest.json"
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
    "Architecture post-Delta field diagnostic node": "∇· / ∇× field diagnostics",
    "Architecture formal field-state node": "ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ → ∇·/∇× field state",
    "Theory divergence symbol row": "∇· / del-dot",
    "Theory curl symbol row": "∇× / del-cross",
    "Theory del-dot alias": "del-dot",
    "Theory del-cross alias": "del-cross",
    "Theory alias definition": "ASCII aliases for <code>∇·</code> and <code>∇×</code>",
    "Theory post-Delta field state": "post-Delta ∇·/∇× field-state diagnostics",
    "Burden target example": "∇·B",
    "Register target example": "∇×ξ",
    "No proof by symbol boundary": "not proof-by-symbol",
}

REQUIRED_PIPELINE_NOTATION_TOKENS = {
    "Standalone pipeline field diagnostic rail": "∇· / ∇× field diagnostics",
    "Standalone pipeline Land before Delta": "Land(B)<br>→ Delta-nB / Delta-kappa",
    "Standalone pipeline post-Delta wording": "target-explicit post-Delta field diagnostics",
}

FORBIDDEN_INDEX_NOTATION_CLAIMS = {
    "∇ replaces Δ": "∇ replaces Δ",
    "nabla replaces Delta": "nabla replaces delta",
    "divergence proves truth": "divergence proves truth",
    "curl proves warrant": "curl proves warrant",
    "∇ truth metric": "∇ truth metric",
    "∇ warrant metric": "∇ warrant metric",
}


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
    for label, phrase in FORBIDDEN_INDEX_NOTATION_CLAIMS.items():
        if phrase in lower and f"not {phrase}" not in lower:
            errors.append(f"docs/index.html contains forbidden notation claim: {label}")


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
