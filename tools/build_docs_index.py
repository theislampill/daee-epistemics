"""Build the generated public docs/index.html control wiki.

The source of truth is the small docs/index/ tree plus owner-derived data from
tracked atomics. docs/index.html is a generated browser surface and should not
be edited directly.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "docs" / "index"
MANIFEST = SOURCE_ROOT / "manifest.json"
OUTPUT = ROOT / "docs" / "index.html"

BANNER = (
    "<!-- GENERATED FILE: do not edit this HTML output directly. "
    "Edit docs/index/** or owner sources, then run python tools/build_docs_index.py. -->"
)
ALLOWED_CLASSIFICATIONS = {
    "OWNER_DERIVED",
    "STRUCTURED_SOURCE_DERIVED",
    "CURATED_SUMMARY_WITH_OWNER_REFERENCES",
    "STATIC_SNAPSHOT",
    "LAYOUT_ONLY",
}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{rel(path)}: JSON parse error: {exc}") from exc


def _declared_path_values(entry: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("owner_sources", "freshness_dependencies", "canonical_sources"):
        raw = entry.get(key, [])
        if isinstance(raw, list):
            values.extend(value for value in raw if isinstance(value, str))
    return values


def expand_declared_path(raw_path: str) -> list[Path]:
    if raw_path.endswith("/**"):
        base = ROOT / raw_path[:-3]
        if not base.exists() or not base.is_dir():
            raise SystemExit(f"{rel(MANIFEST)}: declared path directory missing: {raw_path}")
        matches = sorted(path for path in base.rglob("*") if path.is_file())
        if not matches:
            raise SystemExit(f"{rel(MANIFEST)}: declared path directory has no files: {raw_path}")
        return matches
    if any(token in raw_path for token in ("*", "?", "[")):
        matches = sorted(path for path in ROOT.glob(raw_path) if path.is_file())
        if not matches:
            raise SystemExit(f"{rel(MANIFEST)}: declared path pattern matched no files: {raw_path}")
        return matches
    path = ROOT / raw_path
    if not path.exists():
        raise SystemExit(f"{rel(MANIFEST)}: declared owner/source path missing: {raw_path}")
    if path.is_dir():
        return sorted(child for child in path.rglob("*") if child.is_file())
    return [path]


def validate_classification(entry: dict[str, Any], context: str) -> None:
    classification = entry.get("classification")
    if not isinstance(classification, str) or classification not in ALLOWED_CLASSIFICATIONS:
        raise SystemExit(
            f"{rel(MANIFEST)}: {context}.classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
        )


def section_source(tab: dict[str, Any]) -> str:
    raw = tab.get("section_source", tab.get("source"))
    if not isinstance(raw, str) or not raw:
        raise SystemExit(f"{rel(MANIFEST)}: tab {tab.get('id')!r} missing section_source")
    return raw


def read_manifest() -> dict[str, Any]:
    if not MANIFEST.exists():
        raise SystemExit(f"{rel(MANIFEST)}: missing docs index manifest")
    manifest = read_json(MANIFEST)
    if manifest.get("schema_version") != 1:
        raise SystemExit(f"{rel(MANIFEST)}: schema_version must be 1")
    tabs = manifest.get("tabs")
    if not isinstance(tabs, list) or not tabs:
        raise SystemExit(f"{rel(MANIFEST)}: tabs must be a non-empty list")
    seen: set[str] = set()
    for index, tab in enumerate(tabs):
        if not isinstance(tab, dict):
            raise SystemExit(f"{rel(MANIFEST)}: tabs[{index}] must be an object")
        for key in ("id", "label", "panel", "section_source", "content_source_type"):
            if not isinstance(tab.get(key), str) or not tab[key]:
                raise SystemExit(f"{rel(MANIFEST)}: tabs[{index}].{key} is required")
        validate_classification(tab, f"tabs[{index}]")
        tab_id = tab["id"]
        if tab["panel"] != tab_id:
            raise SystemExit(f"{rel(MANIFEST)}: tabs[{index}].panel must match tab id for current renderer")
        if tab_id in seen:
            raise SystemExit(f"{rel(MANIFEST)}: duplicate tab id {tab_id!r}")
        seen.add(tab_id)
        section_path = ROOT / section_source(tab)
        if not section_path.exists():
            raise SystemExit(f"{rel(MANIFEST)}: tab {tab_id!r} source missing: {section_source(tab)}")
        for declared in _declared_path_values(tab):
            expand_declared_path(declared)
        for block_index, block in enumerate(tab.get("generated_blocks", [])):
            if not isinstance(block, dict):
                raise SystemExit(f"{rel(MANIFEST)}: tabs[{index}].generated_blocks[{block_index}] must be an object")
            validate_classification(block, f"tabs[{index}].generated_blocks[{block_index}]")
            for declared in _declared_path_values(block):
                expand_declared_path(declared)
            owner_source = block.get("owner_source")
            if isinstance(owner_source, str):
                expand_declared_path(owner_source)
    for index, block in enumerate(manifest.get("visible_blocks", [])):
        if not isinstance(block, dict):
            raise SystemExit(f"{rel(MANIFEST)}: visible_blocks[{index}] must be an object")
        validate_classification(block, f"visible_blocks[{index}]")
        for key in ("id", "label", "current_source"):
            if not isinstance(block.get(key), str) or not block[key]:
                raise SystemExit(f"{rel(MANIFEST)}: visible_blocks[{index}].{key} is required")
        expand_declared_path(block["current_source"])
        for declared in _declared_path_values(block):
            expand_declared_path(declared)
    for index, page in enumerate(manifest.get("standalone_pages", [])):
        if not isinstance(page, dict):
            raise SystemExit(f"{rel(MANIFEST)}: standalone_pages[{index}] must be an object")
        validate_classification(page, f"standalone_pages[{index}]")
        for key in ("id", "label", "output", "template"):
            if not isinstance(page.get(key), str) or not page[key]:
                raise SystemExit(f"{rel(MANIFEST)}: standalone_pages[{index}].{key} is required")
        if not (ROOT / page["template"]).exists():
            raise SystemExit(f"{rel(MANIFEST)}: standalone page template missing: {page['template']}")
        for declared in _declared_path_values(page):
            expand_declared_path(declared)
    return manifest


def source_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: rel(p)):
        digest.update(rel(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def manifest_dependency_paths(manifest: dict[str, Any], extra_paths: list[Path] | None = None) -> list[Path]:
    paths: list[Path] = [MANIFEST]
    if extra_paths:
        paths.extend(extra_paths)
    for value in manifest.get("derived_data", {}).values():
        if isinstance(value, str):
            paths.extend(expand_declared_path(value))
    for tab in manifest.get("tabs", []):
        paths.append(ROOT / section_source(tab))
        for declared in _declared_path_values(tab):
            paths.extend(expand_declared_path(declared))
        for block in tab.get("generated_blocks", []):
            for declared in _declared_path_values(block):
                paths.extend(expand_declared_path(declared))
            owner_source = block.get("owner_source")
            if isinstance(owner_source, str):
                paths.extend(expand_declared_path(owner_source))
    for block in manifest.get("visible_blocks", []):
        paths.extend(expand_declared_path(block["current_source"]))
        for declared in _declared_path_values(block):
            paths.extend(expand_declared_path(declared))
    # De-duplicate while preserving deterministic order.
    unique = {path.resolve(): path for path in paths if path.exists() and path.is_file()}
    return [unique[key] for key in sorted(unique, key=lambda p: str(p))]


def load_modules(manifest: dict[str, Any]) -> list[dict[str, str]]:
    owner_path_text = manifest.get("derived_data", {}).get("module_catalogue")
    if not isinstance(owner_path_text, str) or not owner_path_text:
        raise SystemExit(f"{rel(MANIFEST)}: derived_data.module_catalogue is required")
    owner_path = ROOT / owner_path_text
    payload = read_json(owner_path)
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise SystemExit(f"{rel(owner_path)}: expected top-level modules list")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, entry in enumerate(modules):
        if not isinstance(entry, dict):
            raise SystemExit(f"{rel(owner_path)}: modules[{index}] must be an object")
        module_id = entry.get("id")
        module_class = entry.get("module_class")
        path_text = entry.get("path")
        if not all(isinstance(value, str) and value for value in (module_id, module_class, path_text)):
            raise SystemExit(f"{rel(owner_path)}: modules[{index}] missing id/path/module_class")
        if module_id in seen:
            raise SystemExit(f"{rel(owner_path)}: duplicate module id {module_id!r}")
        seen.add(module_id)
        # Catalogue paths are compiled-runtime paths. Resolve them against atomics
        # so the generated page stays bound to tracked source rather than skill/**.
        source_path = ROOT / "atomics" / path_text
        if not source_path.exists():
            raise SystemExit(
                f"{rel(owner_path)}: module {module_id!r} path missing in atomics source: {rel(source_path)}"
            )
        normalized.append(
            {
                "id": module_id,
                "module_class": module_class,
                "path": path_text,
                "source_path": rel(source_path),
            }
        )
    return sorted(normalized, key=lambda item: (item["module_class"], item["id"]))


def render_tabs(tabs: list[dict[str, Any]]) -> str:
    lines = ['<div class="topbar">', '<div class="tabs" role="tablist" aria-label="DAEE wiki sections">']
    for index, tab in enumerate(tabs):
        tab_id = tab["id"]
        classes = "tab active" if index == 0 else "tab"
        selected = "true" if index == 0 else "false"
        tabindex = "" if index == 0 else ' tabindex="-1"'
        lines.append(
            f'<button type="button" id="tab-{html.escape(tab_id)}" class="{classes}" role="tab" '
            f'aria-selected="{selected}" aria-controls="{html.escape(tab_id)}" '
            f'data-tab="{html.escape(tab_id)}"{tabindex}>{html.escape(tab["label"])}</button>'
        )
    lines.extend(["</div>", "</div>"])
    return "\n".join(lines)


def render_sections(tabs: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for index, tab in enumerate(tabs):
        tab_id = tab["id"]
        source = ROOT / section_source(tab)
        classes = "tabsec active" if index == 0 else "tabsec"
        hidden = "" if index == 0 else " hidden"
        body = source.read_text(encoding="utf-8").strip()
        rendered.append(
            f'<section class="{classes}" id="{html.escape(tab_id)}" role="tabpanel" '
            f'aria-labelledby="tab-{html.escape(tab_id)}"{hidden}>\n{body}\n</section>'
        )
    return "\n".join(rendered)


def render_generated_data(manifest: dict[str, Any], modules: list[dict[str, str]]) -> str:
    source_paths = manifest_dependency_paths(manifest, [ROOT / manifest["template"]])
    provenance = {
        "generator": "tools/build_docs_index.py",
        "manifest": rel(MANIFEST),
        "module_catalogue": manifest["derived_data"]["module_catalogue"],
        "source_digest": source_digest(source_paths),
        "section_sources": [section_source(tab) for tab in manifest["tabs"]],
        "standalone_pages": [page["output"] for page in manifest.get("standalone_pages", [])],
    }
    return (
        '<script id="docs-index-generated-data">\n'
        f"window.DOCS_INDEX_PROVENANCE = {json.dumps(provenance, ensure_ascii=False, sort_keys=True)};\n"
        f"window.DOCS_INDEX_MODULE_CATALOGUE = {json.dumps(modules, ensure_ascii=False, sort_keys=True)};\n"
        "</script>"
    )


def render_owner_source_renderer() -> str:
    return r"""function renderOwnerSourceTable(){
  const rows = window.DOCS_INDEX_MODULE_CATALOGUE || [];
  const el = document.getElementById('ownerSourceTable');
  if(!el) return;
  const supportRows = REFS.filter(r=>['runtime governance','diagnostic','TTP/operator','schema'].includes(r.layer)).slice(0,80);
  el.innerHTML = `<h3>Live module catalogue</h3><p class="subtle">Generated from <code>atomics/skill/references/diagnostics/module-catalogue.json</code>; paths resolve to tracked atomics source, while the root <code>skill/</code> directory remains ignored runtime output.</p><table data-owner-source="atomics/skill/references/diagnostics/module-catalogue.json"><thead><tr><th>Module ID</th><th>Class</th><th>Compiled path</th><th>Tracked source</th></tr></thead><tbody>${rows.map(r=>`<tr data-module-id="${esc(r.id)}"><td><code>${esc(r.id)}</code></td><td>${esc(r.module_class)}</td><td><code>${esc(r.path)}</code></td><td><code>${esc(r.source_path)}</code></td></tr>`).join('')}</tbody></table><h3>Complement-bearing source rows</h3><p class="subtle">Curated support map retained from the index source for governance/schema/source navigation. It is not the module-catalogue owner.</p><table><thead><tr><th>Path</th><th>Layer</th><th>Governs</th><th>Concepts</th><th>Operators</th></tr></thead><tbody>${supportRows.map(r=>`<tr><td><code>${esc(r.path)}</code></td><td>${esc(r.layer)}</td><td>${esc(r.governs)}</td><td>${(r.concepts||[]).map(esc).join(', ')}</td><td>${(r.operators||[]).map(esc).join(', ')}</td></tr>`).join('')}</tbody></table>`;
}"""


def build_index(manifest: dict[str, Any]) -> str:
    template_path = ROOT / manifest["template"]
    if not template_path.exists():
        raise SystemExit(f"{rel(template_path)}: missing template")
    modules = load_modules(manifest)
    output = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{ GENERATED_BANNER }}": BANNER,
        "{{ TOPBAR }}": render_tabs(manifest["tabs"]),
        "{{ SECTIONS }}": render_sections(manifest["tabs"]),
        "{{ GENERATED_DATA }}": render_generated_data(manifest, modules),
        "{{ OWNER_SOURCE_RENDERER }}": render_owner_source_renderer(),
    }
    for token, value in replacements.items():
        if token not in output:
            raise SystemExit(f"{rel(template_path)}: missing template token {token}")
        output = output.replace(token, value)
    unresolved = [token for token in ("{{ GENERATED_BANNER }}", "{{ TOPBAR }}", "{{ SECTIONS }}", "{{ GENERATED_DATA }}", "{{ OWNER_SOURCE_RENDERER }}") if token in output]
    if unresolved:
        raise SystemExit(f"{rel(template_path)}: unresolved template tokens: {unresolved}")
    return output


def standalone_page_provenance(manifest: dict[str, Any], page: dict[str, Any]) -> str:
    paths = manifest_dependency_paths(manifest, [ROOT / page["template"]])
    for declared in _declared_path_values(page):
        paths.extend(expand_declared_path(declared))
    # De-duplicate after adding page-specific dependencies.
    unique = {path.resolve(): path for path in paths if path.exists() and path.is_file()}
    paths = [unique[key] for key in sorted(unique, key=lambda p: str(p))]
    provenance = {
        "generator": "tools/build_docs_index.py",
        "manifest": rel(MANIFEST),
        "output": page["output"],
        "classification": page["classification"],
        "owner_sources": page.get("owner_sources", []),
        "source_digest": source_digest(paths),
    }
    return (
        '<script id="docs-pipeline-generated-provenance">\n'
        f"window.DOCS_PIPELINE_PROVENANCE = {json.dumps(provenance, ensure_ascii=False, sort_keys=True)};\n"
        "</script>"
    )


def build_standalone_page(manifest: dict[str, Any], page: dict[str, Any]) -> str:
    template_path = ROOT / page["template"]
    output = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{ GENERATED_BANNER }}": BANNER,
        "{{ PIPELINE_PAGE_PROVENANCE }}": standalone_page_provenance(manifest, page),
    }
    for token, value in replacements.items():
        if token not in output:
            raise SystemExit(f"{rel(template_path)}: missing template token {token}")
        output = output.replace(token, value)
    return output


def build_outputs() -> dict[Path, str]:
    manifest = read_manifest()
    outputs = {OUTPUT: build_index(manifest)}
    for page in manifest.get("standalone_pages", []):
        outputs[ROOT / page["output"]] = build_standalone_page(manifest, page)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if docs/index.html is stale")
    args = parser.parse_args(argv)

    outputs = build_outputs()
    if args.check:
        stale: list[str] = []
        for path, generated in outputs.items():
            if not path.exists():
                stale.append(f"{rel(path)}: missing generated output")
                continue
            current = path.read_text(encoding="utf-8")
            if current != generated:
                stale.append(f"{rel(path)}: stale; run python tools/build_docs_index.py")
        if stale:
            for item in stale:
                print(item)
            return 1
        print("docs index generation freshness: PASS")
        return 0

    for path, generated in outputs.items():
        path.write_text(generated, encoding="utf-8", newline="\n")
    print("docs index build: PASS")
    print(f"Source: {rel(SOURCE_ROOT)}")
    for path in outputs:
        print(f"Output: {rel(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
