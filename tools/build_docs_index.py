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
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in underprovisioned envs
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "docs" / "index"
MANIFEST = SOURCE_ROOT / "manifest.json"
DESIGN_MD = SOURCE_ROOT / "DESIGN.md"
RELEASE_DOWNLOAD = SOURCE_ROOT / "release-download.json"
OUTPUT = ROOT / "docs" / "index.html"
REFERENCE_ROOT = ROOT / "atomics" / "skill" / "references"
REFERENCE_SOURCE_PATHS = [
    ROOT / "atomics" / "skill" / "README.md",
    ROOT / "atomics" / "skill" / "SKILL.md",
]

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


def split_design_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        raise SystemExit(f"{rel(path)}: missing docs/index design source")
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise SystemExit(f"{rel(path)}: DESIGN.md must start with YAML front matter")
    try:
        _, frontmatter, body = raw.split("---", 2)
    except ValueError as exc:
        raise SystemExit(f"{rel(path)}: DESIGN.md missing closing front matter fence") from exc
    try:
        data = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"{rel(path)}: YAML parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{rel(path)}: YAML front matter must be a mapping")
    return data, body


def read_design_system() -> dict[str, Any]:
    design, _body = split_design_frontmatter(DESIGN_MD)
    required = ("colors", "typography", "spacing", "radius", "shadow", "motion", "components")
    for group in required:
        if not isinstance(design.get(group), dict) or not design[group]:
            raise SystemExit(f"{rel(DESIGN_MD)}: missing required token group {group!r}")
    return design


def css_token_name(raw: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", raw)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    return value.strip("-").lower()


def css_var(prefix: str, raw: str) -> str:
    return f"--ds-{prefix}-{css_token_name(raw)}"


def token_path_value(design: dict[str, Any], path: str) -> Any:
    value: Any = design
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise SystemExit(f"{rel(DESIGN_MD)}: token reference {{{path}}} does not resolve")
        value = value[part]
    return value


def resolve_design_value(design: dict[str, Any], value: Any) -> str:
    if not isinstance(value, str):
        return str(value)
    match = re.fullmatch(r"\{([^{}]+)\}", value.strip())
    if match:
        return resolve_design_value(design, token_path_value(design, match.group(1)))
    return value


def component_value(design: dict[str, Any], component: str, key: str, fallback: str) -> str:
    components = design.get("components", {})
    raw = components.get(component, {}).get(key) if isinstance(components, dict) else None
    if raw is None:
        return fallback
    return resolve_design_value(design, raw)


def hex_to_rgb(value: str) -> str:
    raw = value.strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", raw):
        raise SystemExit(f"{rel(DESIGN_MD)}: expected #RRGGBB color, got {value!r}")
    return ",".join(str(int(raw[index : index + 2], 16)) for index in (1, 3, 5))


def render_design_tokens_css(design: dict[str, Any]) -> str:
    colors = design["colors"]
    typography = design["typography"]
    spacing = design["spacing"]
    radius = design["radius"]
    shadow = design["shadow"]
    motion = design["motion"]

    lines: list[str] = [
        "/* docs-index-design-source: docs/index/DESIGN.md */",
        ":root{",
    ]
    for name, value in colors.items():
        if isinstance(value, str):
            lines.append(f"  {css_var('color', name)}:{value};")
            if re.fullmatch(r"#[0-9A-Fa-f]{6}", value.strip()):
                lines.append(f"  {css_var('color', name)}-rgb:{hex_to_rgb(value)};")
    for name, spec in typography.items():
        if isinstance(spec, dict):
            if "fontFamily" in spec:
                lines.append(f"  {css_var('font', name)}:{spec['fontFamily']};")
            for key in ("fontSize", "fontWeight", "lineHeight", "letterSpacing"):
                if key in spec:
                    lines.append(f"  {css_var(f'type-{css_token_name(name)}', key)}:{spec[key]};")
    for group_name, group in (("space", spacing), ("radius", radius), ("shadow", shadow), ("motion", motion)):
        for name, value in group.items():
            lines.append(f"  {css_var(group_name, name)}:{value};")

    carousel = {
        "gap": component_value(design, "architectureCarousel", "gap", "10px"),
        "primary-width": component_value(design, "architectureCarousel", "primaryWidth", "clamp(620px,56vw,900px)"),
        "side-width": component_value(design, "architectureCarousel", "sideWidth", "clamp(170px,14vw,240px)"),
        "far-width": component_value(design, "architectureCarousel", "farWidth", "clamp(112px,9vw,155px)"),
        "preview-source-width": component_value(design, "carouselPreview", "sourceWidth", "560px"),
        "preview-far-source-width": component_value(design, "carouselPreview", "farSourceWidth", "460px"),
        "preview-near-scale": component_value(design, "carouselPreview", "nearScale", ".43"),
        "preview-far-scale": component_value(design, "carouselPreview", "farScale", ".34"),
        "preview-near-slot-height": component_value(design, "carouselPreview", "nearSlotHeight", "430px"),
        "preview-far-slot-height": component_value(design, "carouselPreview", "farSlotHeight", "310px"),
        "preview-near-max-height": component_value(design, "carouselPreview", "nearMaxHeight", "430px"),
        "preview-far-max-height": component_value(design, "carouselPreview", "farMaxHeight", "330px"),
        "preview-opacity": component_value(design, "carouselPreview", "opacity", ".72"),
        "preview-far-opacity": component_value(design, "carouselPreview", "farOpacity", ".52"),
    }
    for name, value in carousel.items():
        lines.append(f"  --ds-carousel-{name}:{value};")

    compatibility = {
        "bg": "var(--ds-color-background)",
        "panel": "var(--ds-color-background-raised)",
        "panel2": "var(--ds-color-surface-raised)",
        "ink": "var(--ds-color-text)",
        "muted": "var(--ds-color-text-muted)",
        "line": "var(--ds-color-border)",
        "blue": "var(--ds-color-info)",
        "green": "var(--ds-color-success)",
        "cyan": "var(--ds-color-cyan)",
        "violet": "var(--ds-color-violet)",
        "orange": "var(--ds-color-warning)",
        "red": "var(--ds-color-danger)",
        "pink": "var(--ds-color-pink)",
        "yellow": "var(--ds-color-yellow)",
        "stage-d0": "var(--ds-color-stage-d0)",
        "stage-psi-n": "var(--ds-color-stage-psi-n)",
        "stage-dsl-ir": "var(--ds-color-stage-dsl-ir)",
        "stage-owner-ttp-delta": "var(--ds-color-stage-owner-ttp-delta)",
        "stage-collapse-restoration": "var(--ds-color-stage-collapse-restoration)",
    }
    for name, value in compatibility.items():
        lines.append(f"  --{name}:{value};")
    for token_name in (
        "stageD0",
        "stagePsiN",
        "stageDslIr",
        "stageOwnerTtpDelta",
        "stageCollapseRestoration",
    ):
        lines.append(f"  --{css_token_name(token_name)}-rgb:{hex_to_rgb(colors[token_name])};")
    lines.append("}")
    return "\n".join(lines)


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
        digest.update(normalized_source_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def normalized_source_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


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


def js_json(payload: object) -> str:
    """Render JSON for a script tag without permitting accidental script close."""

    return json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def reference_paths() -> list[Path]:
    paths = [path for path in REFERENCE_SOURCE_PATHS if path.exists()]
    paths.extend(sorted(REFERENCE_ROOT.rglob("*.md")))
    seen: dict[Path, Path] = {}
    for path in paths:
        seen[path.resolve()] = path
    return [seen[key] for key in sorted(seen, key=lambda item: rel(item))]


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.S)
    if not match:
        return {}
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S)


def reference_title(path: Path, text: str, frontmatter: dict[str, str]) -> str:
    title = frontmatter.get("title")
    if title:
        return title
    body = strip_frontmatter(text)
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return path.stem.replace("-", " ").title()


def reference_layer(path: Path, frontmatter: dict[str, str]) -> str:
    relative = rel(path)
    module_class = frontmatter.get("module_class", "")
    if "references/case-library/" in relative:
        return "case/test"
    if "references/rubrics/" in relative:
        return "runtime governance"
    if "references/procedures/" in relative or "references/tactics/" in relative or "references/techniques/" in relative:
        return "TTP/operator"
    if relative.endswith("/diagnostic-ir.md") or module_class == "schema":
        return "schema"
    if "references/diagnostics/" in relative:
        if any(name in relative for name in ("recursive-state-transitions.md", "routing-precedence.md", "framework-pipeline.md")):
            return "runtime governance"
        return "diagnostic"
    if "references/" in relative:
        return "terminology/reference"
    if relative.endswith(("README.md", "SKILL.md")):
        return "generated artifact"
    return "source document"


def reference_governs(path: Path, text: str, frontmatter: dict[str, str]) -> str:
    relative = rel(path)
    hints = [
        ("diagnostic-ir.md", "IR / dispatch gate"),
        ("recursive-state-transitions.md", "burden cycle / R(H,Delta)"),
        ("diagnostic-render-contract.md", "Layer A / render"),
        ("output-release.md", "release/render governance"),
        ("routing-precedence.md", "routing precedence"),
        ("module-codes.md", "owner identity"),
        ("case-state-schema.md", "case state / schema"),
        ("reason-disambiguation.md", "xi / reason-role"),
        ("foreign-premise-detection.md", "tribunal / criterion"),
        ("noetic-reading-checklist.md", "noetic structure"),
        ("modes-of-concealment.md", "concealment"),
        ("discourse-orientation.md", "discourse orientation"),
        ("pattern-profiling.md", "mu / pattern profile"),
        ("P1-fitrah-restoration.md", "fitrah / restoration"),
        ("P7-restoration-stops.md", "STOP/HOLD/RECURSE/PARTIAL"),
    ]
    for suffix, governs in hints:
        if relative.endswith(suffix):
            return governs
    load_when = frontmatter.get("load_when")
    if load_when:
        return load_when
    lowered = text.lower()
    if "source-status" in lowered:
        return "source-status discipline"
    if "fitrah" in lowered or "fiṭrah" in lowered:
        return "fitrah / proper function"
    if "testimony" in lowered or "transmission" in lowered:
        return "testimony / sigma / xi"
    return "general source"


def reference_data(modules: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    module_id_by_source = {module["source_path"]: module["id"] for module in modules}
    refs: list[dict[str, Any]] = []
    docs: list[dict[str, Any]] = []
    for index, path in enumerate(reference_paths(), start=1):
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        title = reference_title(path, text, frontmatter)
        path_text = rel(path)
        governs = reference_governs(path, text, frontmatter)
        operator = module_id_by_source.get(path_text, frontmatter.get("id") or "—")
        concepts = [governs] if governs != "general source" else ["general source"]
        refs.append(
            {
                "id": index,
                "path": path_text,
                "title": title,
                "role": title,
                "layer": reference_layer(path, frontmatter),
                "governs": governs,
                "concepts": concepts,
                "operators": [operator],
                "lines": len(text.splitlines()),
            }
        )
        docs.append(
            {
                "id": index,
                "rel": path_text,
                "title": title,
                "content": text,
                "html": f'<pre class="sourceSnapshot"><code>{esc(text)}</code></pre>',
                "lines": len(text.splitlines()),
                "search": f"{path_text}\n{title}\n{text}",
            }
        )
    return refs, docs


def render_reference_data(modules: list[dict[str, str]]) -> str:
    refs, docs = reference_data(modules)
    by_layer: dict[str, int] = {}
    by_role: dict[str, int] = {}
    total_lines = 0
    for ref in refs:
        layer = str(ref.get("layer", "source document"))
        role = str(ref.get("role", "source"))
        by_layer[layer] = by_layer.get(layer, 0) + 1
        by_role[role] = by_role.get(role, 0) + 1
        try:
            total_lines += int(ref.get("lines", 0))
        except (TypeError, ValueError):
            pass
    summary = {
        "total_references": len(refs),
        "total_snapshots": len(docs),
        "total_lines": total_lines,
        "by_layer": dict(sorted(by_layer.items())),
        "by_role": dict(sorted(by_role.items())),
    }
    return "\n".join(
        [
            "// Generated from atomics/skill README, SKILL.md, and references/**/*.md by tools/build_docs_index.py.",
            f"const REFS = {js_json(refs)};",
            f"const DOCS = {js_json(docs)};",
            f"const REF_SUMMARY = {js_json(summary)};",
        ]
    )


def load_runtime_architecture(manifest: dict[str, Any]) -> dict[str, Any]:
    """Load the shared runtime architecture projection for docs/index renderings."""

    source_path_text = manifest.get("derived_data", {}).get("runtime_architecture")
    if not isinstance(source_path_text, str) or not source_path_text:
        raise SystemExit(f"{rel(MANIFEST)}: derived_data.runtime_architecture is required")
    source_path = ROOT / source_path_text
    payload = read_json(source_path)
    if payload.get("schema_version") != 1:
        raise SystemExit(f"{rel(source_path)}: schema_version must be 1")
    if payload.get("status") != "shared-runtime-architecture-source":
        raise SystemExit(f"{rel(source_path)}: status must be shared-runtime-architecture-source")
    for key in (
        "rows",
        "stages",
        "theory_cards",
        "theory_card_notation_targets",
        "mapping_rows",
        "notation_lines",
    ):
        if key not in payload:
            raise SystemExit(f"{rel(source_path)}: missing required key {key!r}")
    for owner in payload.get("runtime_owner_sources", []):
        if isinstance(owner, str):
            expand_declared_path(owner)
    return payload


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_runtime_pipeline(
    items: list[dict[str, Any]],
    pipeline_class: str,
    aria: str,
    rendering_id: str,
    visible_label: str,
) -> str:
    pieces: list[str] = [
        f'<div class="v60-pipeline-panel" data-runtime-row-panel="{esc(rendering_id)}" '
        f'data-runtime-pipeline-panel="{esc(rendering_id)}">',
        f'<div class="v60-pipeline-label">{esc(visible_label)}</div>',
        f'<ol class="v60-pipeline-list {pipeline_class}" aria-label="{esc(aria)}" '
        f'data-runtime-rendering="{esc(rendering_id)}" '
        'data-runtime-layout="phase-grouped-vertical-pipeline">'
    ]
    groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]] = []
    for index, item in enumerate(items):
        item_class = str(item.get("class", ""))
        if not groups or groups[-1][0] != item_class:
            groups.append((item_class, []))
        groups[-1][1].append((index, item))

    for group_index, (item_class, group_items) in enumerate(groups):
        phase_break = "true" if group_index > 0 else "false"
        pieces.append(
            f'<li class="v60-pipeline-phase-group {esc(item_class)}" '
            f'data-phase-group="{esc(item_class)}" data-phase-break="{phase_break}">'
            '<div class="v60-phase-flow">'
        )
        for offset, (index, item) in enumerate(group_items):
            title = item.get("title")
            title_attr = f' title="{esc(title)}"' if isinstance(title, str) and title else ""
            pieces.append(
                f'<span class="v60-pipeline-step {esc(item_class)}" data-pipeline-step="{index + 1}"{title_attr}>'
                f'<span class="v60-step-number">{index + 1}</span>'
                f'<span class="v60-step-label">{render_multiline_text(item["label"])}</span>'
                "</span>"
            )
            if offset < len(group_items) - 1:
                pieces.append('<span class="v60-pipeline-arrow" aria-hidden="true">→</span>')
        pieces.append("</div></li>")
    pieces.append("</ol>")
    pieces.append("</div>")
    return "\n".join(pieces)


def render_formal_algebraic_trace(items: list[str]) -> str:
    trace = " → ".join(str(item) for item in items)
    return "\n".join(
        [
            '<div class="v60-formal-trace-copy" data-runtime-rendering="architecture-formal-algebraic-trace" '
            'data-runtime-layout="copyable-formal-algebraic-trace">',
            '<div class="v60-pipeline-label">Formal algebraic trace</div>',
            f'<pre><code>{esc(trace)}</code></pre>',
            "</div>",
        ]
    )


def render_runtime_architecture_rows(arch: dict[str, Any]) -> str:
    rows = arch["rows"]
    formal_trace = rows.get("formal_algebraic_trace") or [
        item.get("label", "") for item in rows.get("formal", []) if isinstance(item, dict)
    ]
    return "\n".join(
        [
            '<div class="runtimeSourceNote" data-surface-role="provenance" data-runtime-architecture-source="docs/index/runtime-architecture.json">',
            "<strong>Shared source:</strong> Architecture cards, paired Architecture pipelines, and Theory notation are generated from "
            '<code>docs/index/runtime-architecture.json</code>, which points back to canonical runtime owners. '
            "Generated HTML is not the owner.",
            "</div>",
            '<div class="v60-pipeline-stack" data-surface-role="focal" aria-label="Canonical runtime paired pipelines" data-runtime-layout="paired-vertical-pipelines">',
            '<div class="v60-pipeline-heading">Architecture pipeline</div>',
            '<div class="v60-pipeline-columns">',
            render_runtime_pipeline(
                rows["runtime"],
                "v60-runtime-pipeline",
                "Plain process reading",
                "architecture-plain-row",
                "Plain/process reading",
            ),
            render_runtime_pipeline(
                rows["formal"],
                "v56-formula-flow v60-formal-pipeline",
                "Formal runtime trace",
                "architecture-formal-row",
                "Formal runtime trace",
            ),
            "</div>",
            render_formal_algebraic_trace([str(item) for item in formal_trace]),
            "</div>",
        ]
    )


def render_terms(terms: list[list[str]]) -> str:
    return "<ul>\n" + "\n".join(
        f"<li><b>{esc(term)}</b> {render_multiline_text(text)}</li>" for term, text in terms
    ) + "\n</ul>"


def render_multiline_text(value: object) -> str:
    lines = str(value).splitlines() or [str(value)]
    return "<br/>".join(esc(line) for line in lines)


def render_proc_flow(steps: list[str]) -> str:
    pieces: list[str] = ['<div class="v21-proc-flow target">']
    for index, step in enumerate(steps):
        pieces.append(f"<div>{esc(step)}</div>")
        if index < len(steps) - 1:
            pieces.append("<span>→</span>")
    pieces.append("</div>")
    return "\n".join(pieces)


def render_field_grid(fields: list[list[str]]) -> str:
    return '<div class="v21-field-grid">\n' + "\n".join(
        f"<div><b>{esc(symbol)}</b><span>{esc(label)}</span><small>{render_multiline_text(detail)}</small></div>"
        for symbol, label, detail in fields
    ) + "\n</div>"


def render_stage_formula(value: object) -> str:
    return f'<div class="v21-stage-formula">{render_multiline_text(value)}</div>'


def render_gate_flow(card: dict[str, Any]) -> str:
    steps = card.get("steps", [])
    checks = card.get("checks", [])
    step_html: list[str] = ['<div class="v54-gate-flow">']
    for index, step in enumerate(steps):
        title, text = step
        step_html.append(f'<div class="v54-gate-step"><h4>{esc(title)}</h4><p>{render_multiline_text(text)}</p></div>')
        if index < len(steps) - 1:
            step_html.append('<div class="v54-gate-arrow">→</div>')
    step_html.append("</div>")
    check_html = "\n".join(
        f'<div class="v54-gate-check"><b>{esc(title)}</b><span>{render_multiline_text(text)}</span></div>'
        for title, text in checks
    )
    return "\n".join(step_html) + (
        '<div class="v54-gate-check-panel"><h4>Gate checks</h4>'
        f'<div class="v54-gate-checks">\n{check_html}\n</div></div>'
    )


def render_reread_gate(card: dict[str, Any]) -> str:
    def reread_formula(value: str) -> str:
        if " ⊢ " not in value:
            return f'<div class="v21-stage-formula">{esc(value)}</div>'
        left, right = value.split(" ⊢ ", 1)
        outcomes = [piece.strip() for piece in right.split(" | ") if piece.strip()]
        outcome_html = "".join(
            (
                f'<span class="v60-decision-outcome">{esc(outcome)}</span>'
                + ('<span class="v60-decision-separator">|</span>' if index < len(outcomes) - 1 else "")
            )
            for index, outcome in enumerate(outcomes)
        )
        return "\n".join(
            [
                '<div class="v21-stage-formula v60-reread-decision-formula" data-reread-decision-formula="stacked">',
                '<div class="v60-reread-signature">',
                f'<span>{esc(left)}</span>',
                '<span class="v60-reread-turnstile">⊢</span>',
                "</div>",
                f'<div class="v60-reread-outcomes" aria-label="Reread decision outcomes">{outcome_html}</div>',
                "</div>",
            ]
        )

    def chip_row(items: list[str], extra_class: str = "") -> str:
        chips = "".join(f'<span class="v60-field-target">{esc(item)}</span>' for item in items)
        classes = "v60-field-chiprow"
        if extra_class:
            classes += f" {extra_class}"
        return f'<div class="{classes}">{chips}</div>'

    def example_chip_grid(items: list[str], split_after: int | None = None) -> str:
        if split_after is None or split_after <= 0 or split_after >= len(items):
            return chip_row(items, "example-chip-grid")
        rows = [items[:split_after], items[split_after:]]
        row_html = "".join(
            '<span class="example-chip-row">'
            + "".join(f'<span class="v60-field-target">{esc(item)}</span>' for item in row)
            + "</span>"
            for row in rows
            if row
        )
        return f'<div class="v60-field-chiprow example-chip-grid" data-example-grid="4-plus-rest">{row_html}</div>'

    def example_group(label: str, items: list[str], meaning: str, aria: str, split_after: int | None = None) -> str:
        return "\n".join(
            [
                f'<div class="v60-field-targets v60-example-group" aria-label="{esc(aria)}">',
                f'<span class="v60-field-heading">{esc(label)}</span>',
                example_chip_grid(items, split_after),
                f'<span class="v60-field-meaning v60-field-description example-chip-description">{esc(meaning)}</span>',
                "</div>",
            ]
        )

    def loopbreak_witness(value: str, grounding: str) -> str:
        if " ⊢ " in value:
            left, right = value.split(" ⊢ ", 1)
        else:
            left, right = value, ""
        operands = [piece.strip() for piece in right.split(" + ") if piece.strip()]
        operand_rows = [operands[:2], operands[2:]]
        operand_html = "".join(
            '<span class="v60-loopbreak-operand-row" data-loopbreak-row="'
            f'{"loop-grounding" if row_index == 0 else "burden-delta-reread"}">'
            + "".join(f'<span class="v60-loopbreak-chip">{esc(piece)}</span>' for piece in row)
            + "</span>"
            for row_index, row in enumerate(operand_rows)
            if row
        )
        grounding_match = re.match(r"^\s*([^{}]+)\{(.+)\}\s*$", grounding)
        if grounding_match:
            grounding_label = grounding_match.group(1).strip()
            members = [piece.strip() for piece in grounding_match.group(2).split(",") if piece.strip()]
        else:
            grounding_label = "G ∈"
            members = [grounding]
        member_html = "".join(f'<span class="v60-grounding-chip">{esc(piece)}</span>' for piece in members)
        license_text = render_multiline_text(
            "LoopBreak is licensed only with an explicit target loop,\n"
            "owner-licensed grounding source, burden/submove, Δ effect,\n"
            "and post-break reread."
        )
        return "\n".join(
            [
                '<div class="v60-field-targets v60-loopbreak-witness" aria-label="LoopBreak witness form">',
                '<span class="v60-field-heading">LOOPBREAK WITNESS</span>',
                '<div class="v60-loopbreak-formula">',
                f'<span class="v60-loopbreak-head">{esc(left)}</span>',
                '<span class="v60-loopbreak-turnstile">⊢</span>',
                f'<span class="v60-loopbreak-operands">{operand_html}</span>',
                "</div>",
                '<div class="v60-grounding-block">',
                f'<span class="v60-grounding-label">{esc(grounding_label)}</span>',
                f'<span class="v60-grounding-members">{member_html}</span>',
                "</div>",
                f'<span class="v60-field-meaning v60-field-wide">{license_text}</span>',
                "</div>",
            ]
        )
    delta_transition_text = render_multiline_text(
        "Burden/submove work changes ΔⁿB and,\nwhere dependency radius changes, Δκ."
    )
    field_diagnostic_text = render_multiline_text(
        "Target-explicit field diagnostics read the Δ-produced\n"
        "noetic/burden/register/route state before reread closure."
    )
    reread_note_text = render_multiline_text(
        "R(H,Δ) rereads the whole live field.\n"
        "Closure is licensed only when residual ∇·/∇× pressure is cleared,\n"
        "integrated, discharged as derivative, held with reason,\n"
        "or carried into RECURSE/PARTIAL."
    )
    examples_note_text = render_multiline_text(
        "Examples are owner-valid only when\n"
        "the target is explicit and control-relevant;\n"
        "they are not decorative symbol variants."
    )
    return "\n".join(
        [
            reread_formula(card["formula"]),
            '<div class="v60-field-diagnostics" aria-label="Field diagnostics after Delta">',
            f'<div class="v60-diagnostic-card"><b>Δ lands transition</b><span>{delta_transition_text}</span></div>',
            f'<div class="v60-diagnostic-card"><b>∇· / ∇× read after Δ</b><span>{field_diagnostic_text}</span></div>',
            '<div class="v60-field-targets v60-field-grammar" aria-label="Target grammar for field diagnostics">',
            '<span class="v60-field-heading">Target grammar</span>',
            chip_row(["∇·T", "∇×T"]),
            f'<span class="v60-field-meaning v60-field-description">{esc(card["target_grammar"])}</span>',
            "</div>",
            example_group(
                "∇· EXAMPLES",
                card["divergence_examples"],
                "residual outward pressure in an explicit target field",
                "Readable divergence examples",
                4,
            ),
            example_group(
                "∇× EXAMPLES",
                card["curl_examples"],
                "circular / rotational dependency in an explicit target field",
                "Readable curl examples",
                4,
            ),
            f'<div class="v60-diagnostic-note">{examples_note_text}</div>',
            loopbreak_witness(card["loopbreak_witness"], card["grounding_grammar"]),
            f'<div class="v60-diagnostic-note">{reread_note_text}</div>',
            "</div>",
        ]
    )


def render_decision(card: dict[str, Any]) -> str:
    return "\n".join(
        [
            '<div class="v21-dec-grid v62-decision-grid" data-decision-layout="2x2-plus-complete">',
            '<div class="recurse">↻<br/>RECURSE</div>',
            '<div class="hold">–<br/>HOLD</div>',
            '<div class="partial">○<br/>PARTIAL</div>',
            '<div class="stop">■<br/>STOP</div>',
            '<div class="complete">✓<br/>COMPLETE</div>',
            "</div>",
            f'<div class="v21-note"><b>Correct recurse:</b> {render_multiline_text(card["note"])}</div>',
        ]
    )


def render_architecture_subcard(card: dict[str, Any]) -> str:
    kind = card.get("kind")
    base_class = "v21-note" if kind == "note" else "v21-card"
    classes = [base_class]
    if kind == "warning":
        classes.append("v21-warn")
    if kind == "resolution":
        classes.append("v21-purple")
    if card.get("reread_phase"):
        classes.append("v60-reread-phase")
    classes.append("v60-selectable-subcard")
    attrs = f'class="{" ".join(classes)}" data-substage-key="{esc(card["key"])}" role="button" tabindex="0"'
    title = f'<h3>{esc(card["title"])}</h3>' if kind != "note" else f'<b>{esc(card["title"])}:</b> '
    if kind in {"terms", "warning"}:
        content = render_terms(card.get("terms", [])) if kind == "terms" else f"<p>{render_multiline_text(card['text'])}</p>"
    elif kind == "note":
        note_text = str(card["text"])
        separator = "<br/>" if "\n" in note_text else " "
        return f'<div {attrs}>{title}{separator}{render_multiline_text(note_text)}</div>'
    elif kind == "proc_flow":
        content = render_proc_flow(card.get("steps", []))
    elif kind == "field_grid":
        intro = str(card["intro"])
        if " names " in intro:
            formula, rest = intro.split(" names ", 1)
            intro_html = f"<p><code>{esc(formula)}</code><br/>names {render_multiline_text(rest)}</p>"
        else:
            intro_html = f"<p>{render_multiline_text(intro)}</p>"
        content = intro_html + render_field_grid(card.get("fields", []))
    elif kind == "gate_flow":
        content = render_gate_flow(card)
    elif kind == "formula":
        content = render_stage_formula(card["formula"])
    elif kind == "formula_terms":
        content = f'{render_stage_formula(card["formula"])}{render_terms(card.get("terms", []))}'
    elif kind == "reread_gate":
        content = render_reread_gate(card)
    elif kind == "decision":
        content = render_decision(card)
    elif kind == "resolution":
        content = f'{render_stage_formula(card["formula"])}{render_terms(card.get("terms", []))}'
    else:
        raise SystemExit(f"{rel(ROOT / 'docs/index/runtime-architecture.json')}: unknown subcard kind {kind!r}")
    return f"<div {attrs}>{title}{content}</div>"


def render_architecture_stage_body(stage: dict[str, Any]) -> str:
    subcards = stage.get("subcards", [])
    if stage.get("key") == "ir":
        left_keys = {"diagnostic-reduction-order", "ir-control-surface"}
        right_keys = {"gate-owner-layerb"}
        left = [card for card in subcards if card.get("key") in left_keys]
        right = [card for card in subcards if card.get("key") in right_keys]
        return "\n".join(
            [
                '<div class="v63-two-column-stage-layout v63-ir-layout" data-stage-layout="ir-two-left-one-right">',
                '<div class="v63-stage-stack v63-stage-stack-left" data-stage-layout-column="left">',
                *(render_architecture_subcard(card) for card in left),
                "</div>",
                '<div class="v63-stage-stack v63-stage-stack-right" data-stage-layout-column="right">',
                *(render_architecture_subcard(card) for card in right),
                "</div>",
                "</div>",
            ]
        )
    if stage.get("key") == "ownerRelease":
        left_keys = {"operator-signature", "strict-burden-cycle"}
        right_keys = {"reread-gate", "decision"}
        left = [card for card in subcards if card.get("key") in left_keys]
        right = [card for card in subcards if card.get("key") in right_keys]
        return "\n".join(
            [
                '<div class="v63-two-column-stage-layout v63-owner-release-layout" data-stage-layout="owner-release-two-by-two">',
                '<div class="v63-stage-stack v63-stage-stack-left" data-stage-layout-column="left">',
                *(render_architecture_subcard(card) for card in left),
                "</div>",
                '<div class="v63-stage-stack v63-stage-stack-right" data-stage-layout-column="right">',
                *(render_architecture_subcard(card) for card in right),
                "</div>",
                "</div>",
            ]
        )
    return "\n".join(render_architecture_subcard(card) for card in subcards)


def render_runtime_architecture_cards(arch: dict[str, Any]) -> str:
    articles: list[str] = [
        '<div class="v30-click-hint">Select a bridge stage panel below to inspect its audit trace.</div>',
        '<div class="v60-architecture-carousel" data-carousel="architecture-runtime">',
        '<div class="v60-carousel-controls" aria-label="Architecture carousel controls">',
        '<button class="v60-carousel-btn" type="button" data-carousel-action="prev" '
        'aria-label="Previous architecture stage">‹</button>',
        '<div class="v60-carousel-status" id="architectureCarouselStatus" aria-live="polite" '
        'aria-label="Select architecture stage">',
        '<span class="v60-carousel-status-label">Stage 1 of 5</span>',
        '<div class="v60-carousel-dots" aria-label="Select architecture stage">',
    ]
    for index, stage in enumerate(arch["stages"]):
        title = re.sub(r"<[^>]+>", "", str(stage.get("title_html") or stage.get("title", "")))
        current = ' aria-current="true"' if index == 0 else ""
        articles.append(
            f'<button class="v60-carousel-dot" type="button" data-carousel-target="{esc(stage["key"])}" '
            f'aria-label="Show stage {esc(stage["number"])}: {esc(title)}"{current}>'
            f'<span>{esc(stage["number"])}</span></button>'
        )
    articles.extend(
        [
            "</div>",
            "</div>",
        '<button class="v60-carousel-btn" type="button" data-carousel-action="next" '
        'aria-label="Next architecture stage">›</button>',
        "</div>",
        '<div class="v21-five-col v60-architecture-rail" data-pipeline="target" '
        'aria-label="Architecture runtime cards" role="listbox" aria-orientation="horizontal" '
        'tabindex="0">',
        ]
    )
    default_positions = ["center", "next", "far-next", "far-prev", "prev"]
    for index, stage in enumerate(arch["stages"]):
        title = stage.get("title_html", esc(stage.get("title", "")))
        active_class = " v30-active" if index == 0 else ""
        position = default_positions[index] if index < len(default_positions) else "far"
        preview_class = " is-primary" if position == "center" else f" is-preview is-{position}"
        selected = "true" if index == 0 else "false"
        tabindex = "0" if index == 0 else "-1"
        articles.append(
            f'<div class="v60-carousel-slot{preview_class}" data-carousel-slot '
            f'data-stage-key="{esc(stage["key"])}" data-carousel-index="{index}" '
            f'data-carousel-position="{position}">'
        )
        articles.append(
            f'<article class="v21-stage {esc(stage["class"])} v30-selectable-stage v60-carousel-card{active_class}{preview_class}" '
            f'data-pipeline="target" data-stage-key="{esc(stage["key"])}" '
            f'data-carousel-index="{index}" data-carousel-position="{position}" '
            f'role="option" aria-selected="{selected}" tabindex="{tabindex}">'
            f"<h2>{title}</h2>"
        )
        articles.append(render_architecture_stage_body(stage))
        articles.append("</article></div>")
    articles.append("</div>")
    articles.extend(
        [
            "</div>",
            "<noscript><style>"
            "#architecture #canonical-architecture-runtime .v60-architecture-rail{display:grid!important;"
            "grid-template-columns:repeat(auto-fit,minmax(300px,1fr))!important;overflow:visible!important}"
            "#architecture #canonical-architecture-runtime .v60-carousel-controls,"
            "#architecture #canonical-architecture-runtime .v60-carousel-dots{display:none!important}"
            "#architecture #canonical-architecture-runtime .v60-carousel-card{display:block!important;"
            "transform:none!important;opacity:1!important;max-height:none!important}"
            "#architecture #canonical-architecture-runtime .v60-carousel-slot{display:block!important;"
            "width:auto!important;height:auto!important;overflow:visible!important}"
            "#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard{display:block!important}"
            "</style></noscript>",
            '<div aria-live="polite" class="v30-stage-detail panel" id="targetStaticStageDetail"></div>',
        ]
    )
    return "\n".join(articles)


def js_array(values: list[str]) -> str:
    def js_single(value: str) -> str:
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"

    return "[" + ",".join(js_single(str(value)) for value in values) + "]"


def notation_token_ids(arch: dict[str, Any]) -> set[str]:
    token_ids: set[str] = set()
    for line in arch.get("notation_lines", []):
        if not isinstance(line, list):
            continue
        for segment in line:
            if isinstance(segment, dict) and isinstance(segment.get("token"), str):
                token_ids.add(segment["token"])
    return token_ids


def theory_card_targets(arch: dict[str, Any], card: dict[str, Any]) -> list[str]:
    target_map = arch.get("theory_card_notation_targets")
    if not isinstance(target_map, dict):
        raise SystemExit("docs/index/runtime-architecture.json: theory_card_notation_targets must be an object")
    card_id = str(card.get("id", ""))
    targets = target_map.get(card_id)
    if not isinstance(targets, list) or not targets or not all(isinstance(target, str) for target in targets):
        raise SystemExit(
            "docs/index/runtime-architecture.json: "
            f"theory card {card_id!r} must declare at least one notation target"
        )
    known_tokens = notation_token_ids(arch)
    missing = sorted(target for target in targets if target not in known_tokens)
    if missing:
        raise SystemExit(
            "docs/index/runtime-architecture.json: "
            f"theory card {card_id!r} targets missing notation tokens {missing!r}"
        )
    return targets


CONTROL_CARD_TOKEN_ALIASES = {
    "τ": "tau",
    "σ": "sigma",
    "ξ": "xi",
    "Ω": "omega",
    "μ": "mu",
    "κ": "kappa",
}


def notation_phase_classes(arch: dict[str, Any]) -> dict[str, str]:
    """Derive notation chip colors from the same phase classes as Theory cards."""

    phase_for_token = {
        "D0": "phase-input",
        "noetic": "phase-layer-a",
        "Psi": "phase-layer-a",
        "m": "phase-layer-a",
        "N": "phase-gate",
        "tau": "phase-gate",
        "sigma": "phase-gate",
        "heart": "phase-gate",
        "xi": "phase-gate",
        "omega": "phase-gate",
        "mu": "phase-gate",
        "IR": "phase-gate",
        "gradient": "phase-gate",
        "kappa": "phase-reread-closure",
        "H": "phase-reread-closure",
        "burden": "phase-owner-delta",
        "submoves": "phase-owner-delta",
        "Land": "phase-owner-delta",
        "deltaB": "phase-owner-delta",
        "deltaK": "phase-reread-closure",
        "nablaDot": "phase-owner-delta",
        "nablaCross": "phase-owner-delta",
        "fieldDiagnostics": "phase-owner-delta",
        "loopBreak": "phase-owner-delta",
        "R": "phase-reread-closure",
        "C": "phase-reread-closure",
        "final": "phase-reread-closure",
        "nextB": "phase-reread-closure",
        "coupling": "phase-public-boundary",
        "PsiI": "phase-public-boundary",
    }
    known_tokens = notation_token_ids(arch)
    for card in arch.get("theory_cards", []):
        if not isinstance(card, dict):
            continue
        phase_class = str(card.get("phase_class", ""))
        if not phase_class.startswith("phase-"):
            continue
        targets = theory_card_targets(arch, card)
        card_id = str(card.get("id", ""))
        primary = CONTROL_CARD_TOKEN_ALIASES.get(card_id, card_id)
        if primary not in targets or primary not in known_tokens:
            primary = targets[0]
        phase_for_token[primary] = phase_class
    return phase_for_token


def notation_metadata(arch: dict[str, Any]) -> dict[str, dict[str, object]]:
    """Join notation chip data to mapping rows for the Theory context panel."""

    mapping_rows = arch.get("mapping_rows")
    if not isinstance(mapping_rows, list) or len(mapping_rows) < 11:
        raise SystemExit("docs/index/runtime-architecture.json: mapping_rows must define the runtime sequence")

    row_for_token = {
        "D0": 0,
        "noetic": 1,
        "Psi": 1,
        "N": 1,
        "m": 1,
        "tau": 1,
        "sigma": 1,
        "heart": 1,
        "xi": 1,
        "omega": 1,
        "mu": 1,
        "kappa": 1,
        "H": 1,
        "IR": 2,
        "gradient": 3,
        "burden": 4,
        "submoves": 4,
        "Land": 5,
        "deltaB": 5,
        "deltaK": 5,
        "nablaDot": 6,
        "nablaCross": 6,
        "fieldDiagnostics": 6,
        "loopBreak": 7,
        "R": 8,
        "C": 9,
        "final": 9,
        "nextB": 9,
        "coupling": 10,
        "PsiI": 10,
    }
    phase_for_token = notation_phase_classes(arch)

    metadata: dict[str, dict[str, object]] = {}
    for line in arch.get("notation_lines", []):
        if not isinstance(line, list):
            continue
        for segment in line:
            if not isinstance(segment, dict):
                continue
            token = segment.get("token")
            if not isinstance(token, str):
                continue
            row_index = row_for_token.get(token)
            role = str(segment.get("label", ""))
            owners = "docs/index/runtime-architecture.json"
            if row_index is not None:
                row = mapping_rows[row_index]
                if isinstance(row, list) and len(row) == 3:
                    role = str(row[1])
                    owners = str(row[2])
            related_targets = [
                str(value)
                for value in segment.get("highlight", [])
                if isinstance(value, str) and value != token
            ]
            metadata[token] = {
                "symbol": str(segment.get("symbol", token)),
                "meaning": str(segment.get("label", token)),
                "runtime_role": role,
                "source_owners": owners,
                "related_targets": related_targets,
                "phase_class": phase_for_token.get(token, "phase-layer-a"),
            }
    return metadata


def render_theory_control_overview(arch: dict[str, Any]) -> str:
    metadata = notation_metadata(arch)
    pieces: list[str] = [
        '<div class="runtimeSourceNote theoryRuntimeSourcing" data-surface-role="provenance" data-runtime-architecture-source="docs/index/runtime-architecture.json">',
        "<strong>Same runtime sequence, formalized:</strong> this tab renders compact notation chips and mapping rows from the same shared runtime architecture source as the Architecture tab, without duplicating the Architecture pipelines.",
        "</div>",
        '<div class="theoryFocalGrid" data-surface-role="focal" data-primary-focal="true">',
        '<div class="notationBoard" id="notationBoard" '
        'data-runtime-rendering="theory-formalism-notation">',
    ]
    for line in arch["notation_lines"]:
        pieces.append('<div class="notationLine">')
        for segment in line:
            if "token" in segment:
                classes = "ntok"
                if segment.get("classes"):
                    classes += f' {esc(segment["classes"])}'
                phase_class = str(metadata.get(segment["token"], {}).get("phase_class", "phase-layer-a"))
                classes += f" {esc(phase_class)}"
                pieces.append(
                    f'<span class="{classes}" data-k="{esc(segment["token"])}" '
                    f'data-notation-id="{esc(segment["token"])}" role="button" tabindex="0" '
                    'aria-pressed="false" '
                    f'data-label="{esc(segment["label"])}" '
                    f'data-meaning="{esc(str(metadata.get(segment["token"], {}).get("meaning", segment["label"])))}" '
                    f'data-runtime-role="{esc(str(metadata.get(segment["token"], {}).get("runtime_role", segment["label"])))}" '
                    f'data-source-owners="{esc(str(metadata.get(segment["token"], {}).get("source_owners", "docs/index/runtime-architecture.json")))}" '
                    f'data-related-targets="{esc(" ".join(str(value) for value in metadata.get(segment["token"], {}).get("related_targets", [])))}" '
                    'onkeydown="return activateNotationToken(event,this)" '
                    f'onclick="highlightNotation({js_array(segment["highlight"])}, \'{esc(segment["token"])}\')">{esc(segment["symbol"])}</span>'
                )
            else:
                cls = f' class="{esc(segment["class"])}"' if segment.get("class") else ""
                pieces.append(f'<span{cls}>{esc(segment["text"])}</span>')
        pieces.append("</div>")
    pieces.append("</div>")
    pieces.append(
        '<aside class="notationExplain theoryNotationContext" id="notationExplain" '
        'data-surface-role="support" aria-live="polite">'
        '<div class="notationContext"><div class="notationContextHeader">'
        '<span>Highlighted notation</span><span class="ntokMini">select a chip</span>'
        '</div><div class="notationContextBlock"><strong>Start here</strong>'
        '<span>Click a notation chip or runtime card to inspect meaning, runtime role, source owners, and related notation without replacing the formal symbols.</span>'
        "</div></div></aside>"
    )
    pieces.append("</div>")

    theory_cards = list(arch["theory_cards"])
    phase_legend: dict[str, dict[str, Any]] = {}
    for card in theory_cards:
        card_id = str(card.get("id", ""))
        phase_id = str(card.get("phase_id", "")).strip()
        phase_label = str(card.get("phase_label", "")).strip()
        if not phase_id or not phase_label:
            raise SystemExit(
                "docs/index/runtime-architecture.json: theory card "
                f"{card_id!r} must declare phase_id and phase_label"
            )
        if "phase_order" not in card or "card_runtime_order" not in card:
            raise SystemExit(
                "docs/index/runtime-architecture.json: theory card "
                f"{card_id!r} must declare phase_order and card_runtime_order"
            )
        if not str(card.get("runtime_step_group", "")).strip() or not str(card.get("runtime_step_label", "")).strip():
            raise SystemExit(
                "docs/index/runtime-architecture.json: theory card "
                f"{card_id!r} must declare runtime_step_group and runtime_step_label"
            )
        phase = phase_legend.setdefault(
            phase_id,
            {
                "label": phase_label,
                "order": int(card["phase_order"]),
                "phase_class": str(card.get("phase_class", "phase-layer-a")),
            },
        )
        if phase["label"] != phase_label or phase["order"] != int(card["phase_order"]):
            raise SystemExit(
                "docs/index/runtime-architecture.json: theory card "
                f"{card_id!r} has conflicting metadata for phase {phase_id!r}"
            )
    sorted_phase_legend = sorted(
        (data | {"id": phase_id} for phase_id, data in phase_legend.items()),
        key=lambda phase: int(phase["order"]),
    )
    pieces.append(
        '<section class="panel theoryCardBank" data-surface-role="control" '
        'data-theory-card-bank="runtime-notation-controls">'
        '<div class="surfaceRoleKicker">Runtime execution flow</div>'
        '<h2>Runtime notation controls</h2>'
        '<p class="subtle">Cards stay in source-owned execution order. Small runtime step breaks make the sequence readable; color comes from the side legend.</p>'
        '<div class="theoryRuntimeWorkspace">'
        '<aside class="theoryPhaseLegend" data-surface-role="support" '
        'data-theory-phase-legend="semantic-color" aria-label="Phase color legend">'
        '<div class="surfaceRoleKicker">Phase / color legend</div>'
    )
    for phase in sorted_phase_legend:
        pieces.append(
            f'<div class="theoryPhaseLegendItem {esc(str(phase["phase_class"]))}" '
            f'data-theory-phase-id="{esc(str(phase["id"]))}" '
            f'data-theory-phase-order="{esc(str(phase["order"]))}">'
            '<span class="phaseDot" aria-hidden="true"></span>'
            f'<span>{esc(str(phase["label"]))}</span>'
            '</div>'
        )
    pieces.append(
        '</aside>'
        '<div class="theoryCardFlow" data-theory-card-flow="runtime-execution">'
    )
    sorted_cards = sorted(theory_cards, key=lambda card: int(card["card_runtime_order"]))
    seen_step_groups: set[str] = set()
    current_step_group = None
    for index, card in enumerate(sorted_cards):
        step_group = str(card["runtime_step_group"])
        step_label = str(card["runtime_step_label"])
        if step_group != current_step_group:
            if step_group in seen_step_groups:
                raise SystemExit(
                    "docs/index/runtime-architecture.json: runtime_step_group "
                    f"{step_group!r} is not contiguous in card_runtime_order"
                )
            seen_step_groups.add(step_group)
            current_step_group = step_group
            pieces.append(
                f'<div class="runtimeStepBreak" data-runtime-step-group="{esc(step_group)}" '
                f'data-runtime-step-label="{esc(step_label)}">'
                '<span class="runtimeStepRule" aria-hidden="true"></span>'
                f'<span>{esc(step_label)}</span>'
                '<span class="runtimeStepRule" aria-hidden="true"></span>'
                '</div>'
            )
        extra = f' {esc(card.get("extra_class", ""))}' if card.get("extra_class") else ""
        targets = theory_card_targets(arch, card)
        active_class = " is-linked-active" if index == 0 else ""
        pressed = "true" if index == 0 else "false"
        pieces.append(
            f'<button type="button" class="controlCard {esc(card["phase_class"])}{extra}{active_class}" '
            f'data-theory-card="{esc(card["id"])}" data-concept-id="{esc(card["id"])}" '
            f'data-phase-id="{esc(str(card["phase_id"]))}" '
            f'data-phase-label="{esc(str(card["phase_label"]))}" '
            f'data-phase-order="{esc(str(card["phase_order"]))}" '
            f'data-card-runtime-order="{esc(str(card["card_runtime_order"]))}" '
            f'data-runtime-step-group="{esc(step_group)}" '
            f'data-runtime-step-label="{esc(step_label)}" '
            f'data-notation-targets="{esc(" ".join(targets))}" '
            'data-runtime-architecture-source="docs/index/runtime-architecture.json" '
            f'title="Phase: {esc(str(card["phase_label"]))}; runtime step: {esc(step_label)}" '
            f'aria-label="{esc(card["symbol"])}: {esc(card["label"])}. Phase: {esc(str(card["phase_label"]))}. Runtime step: {esc(step_label)}." '
            f'aria-pressed="{pressed}" onclick="selectTheoryCard(this)" onkeydown="return activateTheoryCard(event,this)">\n'
            f'<span class="controlSym">{esc(card["symbol"])}</span>\n'
            f'<strong>{esc(card["label"])}</strong>\n'
            f'<p>{esc(card["description"])}</p>\n'
            "</button>"
        )
    pieces.append("</div></div></section>")
    pieces.extend(
        [
            '<div class="notationLegend" data-surface-role="support">',
            '<div class="miniCard"><strong>𝓝 → N:</strong><span>design covers the possible noetic-structure selection space;</span><span>runtime selects or holds the live N from D₀ → Ψᴺ.</span></div>',
            '<div class="miniCard"><strong>Registers:</strong><span>N,m,τ,σ,♥,ξ,Ω,μ,κ,H</span><span>are the state components being diagnosed.</span></div>',
            '<div class="miniCard"><strong>Route-gradient:</strong><span>∇ orders eligible route pressure</span><span>after IR/routing/catalogue gates;</span><span>it never replaces those gates or Δ.</span></div>',
            '<div class="miniCard"><strong>Phase discipline:</strong><span>∇ ranks eligible route pressure before release.</span><span>Δ produces the changed field state.</span><span>∇·T / ∇×T diagnose</span><span>target-explicit post-Δ field pressure.</span><span>R(H,Δ) rereads the changed field.</span><span>𝒞(Ψᴺ) licenses closure as field condition.</span><span>T_lang: Ψᴺ ⇢ Ψᴵ marks public coupling</span><span>without guaranteed uptake.</span></div>',
            '<div class="miniCard"><strong>Burden cycle:</strong><span>ⁿB contains ⁿBᵢ[OPᵢ] submoves;</span><span>landing produces ΔⁿB/Δκ</span><span>and post-Delta ∇·/∇× field-state diagnostics.</span></div>',
            '<div class="miniCard"><strong>Loop-breaking:</strong> LoopBreak(∇×T) is licensed only when nonzero curl has an owner-grounded target and Δ effect.</div>',
            '<div class="miniCard"><strong>Resolution:</strong><span>R decides STOP/HOLD/PARTIAL/ⁿ⁺¹B;</span><span>𝒞(Ψᴺ) is a positive closure-field condition,</span><span>not checklist exhaustion.</span></div>',
            '<div class="miniCard"><strong>Output boundary:</strong><span>T_lang: Ψᴺ ⇢ Ψᴵ names the public release relation</span><span>after closure/hold/partial;</span><span>it is not part of the burden loop</span><span>and does not claim guaranteed uptake.</span></div>',
            "</div>",
            render_theory_mapping_table(arch),
        ]
    )
    return "\n".join(pieces)


def render_theory_mapping_table(arch: dict[str, Any]) -> str:
    rows = "\n".join(
        f"<tr><td><code>{esc(notation)}</code></td><td>{esc(role)}</td><td><code>{esc(owner)}</code></td></tr>"
        for notation, role, owner in arch["mapping_rows"]
    )
    return (
        '<template class="theoryNotationMapData" data-hidden-source-map="true" data-runtime-architecture-source="docs/index/runtime-architecture.json" '
        'data-runtime-rendering="theory-formalism-mapping">'
        f"<table><thead><tr><th>Notation</th><th>Runtime role</th><th>Source owner</th></tr></thead><tbody>{rows}</tbody></table>"
        "</template>"
    )


def render_theory_bridge_compact(arch: dict[str, Any]) -> str:
    chips = "".join(
        f'<span class="notationChip"><span class="nsym">{esc(row[0])}</span><span class="nlabel">{esc(row[1])}</span></span>'
        for row in arch["mapping_rows"]
    )
    return (
        '<div class="bridgeFlow compactBridgeFlow" aria-label="Shared runtime architecture notation chips">'
        f"{chips}"
        "</div>"
        '<p class="subtle">Generated from <code>docs/index/runtime-architecture.json</code>. This compact chip rail names the same sequence; the Architecture tab owns the expanded visual cards and rows.</p>'
    )


def render_theory_final_runtime_summary(arch: dict[str, Any]) -> str:
    return (
        '<section id="pv-final">'
        "<h2>20. Final runtime notation</h2>"
        "<p>The final notation source map is generated as hidden metadata from the shared runtime architecture source and surfaced through the contextual Highlighted notation panel, not as a dominant table or a second copy of the Architecture-tab rows.</p>"
        f"{render_theory_mapping_table(arch)}"
        "<p>Select a notation chip or theory card to inspect the relevant runtime role and source owner. Every symbol either affects diagnosis, routing, owner execution, state landing, dependency reread, auditability, or the framework graphic. Nothing is merely decorative.</p>"
        "</section>"
    )


def replace_section_tokens(body: str, arch: dict[str, Any]) -> str:
    replacements = {
        "{{ RUNTIME_ARCHITECTURE_ROWS }}": render_runtime_architecture_rows(arch),
        "{{ RUNTIME_ARCHITECTURE_CARDS }}": render_runtime_architecture_cards(arch),
        "{{ THEORY_RUNTIME_OVERVIEW }}": render_theory_control_overview(arch),
        "{{ THEORY_BRIDGE_COMPACT }}": render_theory_bridge_compact(arch),
        "{{ THEORY_FINAL_RUNTIME_SUMMARY }}": render_theory_final_runtime_summary(arch),
    }
    for token, value in replacements.items():
        body = body.replace(token, value)
    unresolved = [token for token in replacements if token in body]
    if unresolved:
        raise SystemExit(f"{rel(MANIFEST)}: unresolved section tokens: {unresolved}")
    return body


def release_download_metadata_path(manifest: dict[str, Any]) -> Path:
    raw = manifest.get("derived_data", {}).get("release_download")
    if isinstance(raw, str) and raw:
        return ROOT / raw
    return RELEASE_DOWNLOAD


def fallback_release_download_metadata() -> dict[str, Any]:
    return {
        "download_kind": "latest_release_page",
        "release_title": "Latest GitHub Release",
        "release_url": "https://github.com/theislampill/daee-epistemics/releases/latest",
        "fallback_url": "https://github.com/theislampill/daee-epistemics/releases/latest",
        "primary_skill_asset_name": "",
        "primary_skill_asset_browser_download_url": "",
        "sha256": "",
    }


def read_release_download_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    path = release_download_metadata_path(manifest)
    if not path.exists():
        return fallback_release_download_metadata()
    metadata = read_json(path)
    if not isinstance(metadata, dict):
        raise SystemExit(f"{rel(path)}: release download metadata must be a JSON object")
    if metadata.get("schema_version") != 1:
        raise SystemExit(f"{rel(path)}: schema_version must be 1")
    return metadata


def render_download_nav_action(metadata: dict[str, Any]) -> str:
    direct_url = str(metadata.get("primary_skill_asset_browser_download_url") or "").strip()
    fallback_url = str(metadata.get("fallback_url") or metadata.get("release_url") or "").strip()
    href = direct_url or fallback_url or "https://github.com/theislampill/daee-epistemics/releases/latest"
    direct = bool(direct_url)
    label = "Download latest .skill" if direct else "Latest release"
    title = "Latest GitHub Release"
    release_title = str(metadata.get("release_title") or "").strip()
    if release_title:
        title = f"{title}: {release_title}"
    sha = str(metadata.get("sha256") or "").strip().upper()
    asset_name = str(metadata.get("primary_skill_asset_name") or "").strip()
    data_kind = str(metadata.get("download_kind") or ("direct_asset" if direct else "latest_release_page"))
    aria = "Download latest .skill asset from GitHub Release" if direct else "Open latest GitHub Release"
    download_attr = f' download="{html.escape(asset_name, quote=True)}"' if direct and asset_name.endswith(".skill") else ""
    return (
        '<a class="downloadNavAction" data-release-download-kind="'
        f'{html.escape(data_kind, quote=True)}" data-release-sha256="{html.escape(sha, quote=True)}" '
        f'href="{html.escape(href, quote=True)}" target="_blank" rel="noopener" '
        f'title="{html.escape(title, quote=True)}" aria-label="{html.escape(aria, quote=True)}"{download_attr}>'
        f'<span>{html.escape(label)}</span>'
        "</a>"
    )


def render_tabs(tabs: list[dict[str, Any]], release_download: dict[str, Any]) -> str:
    lines = [
        '<div class="topbar">',
        '<div class="topbarInner">',
        '<div class="tabs" role="tablist" aria-label="DAEE wiki sections">',
    ]
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
    lines.extend(["</div>", render_download_nav_action(release_download), "</div>", "</div>"])
    return "\n".join(lines)


def render_sections(tabs: list[dict[str, Any]], arch: dict[str, Any]) -> str:
    rendered: list[str] = []
    for index, tab in enumerate(tabs):
        tab_id = tab["id"]
        source = ROOT / section_source(tab)
        classes = "tabsec active" if index == 0 else "tabsec"
        hidden = "" if index == 0 else " hidden"
        body = replace_section_tokens(source.read_text(encoding="utf-8").strip(), arch)
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
        "design_source": rel(DESIGN_MD),
        "module_catalogue": manifest["derived_data"]["module_catalogue"],
        "release_download": manifest["derived_data"].get("release_download"),
        "source_digest": source_digest(source_paths),
        "section_sources": [section_source(tab) for tab in manifest["tabs"]],
        "standalone_pages": [page["output"] for page in manifest.get("standalone_pages", [])],
    }
    return (
        '<script id="docs-index-generated-data">\n'
        f"window.DOCS_INDEX_PROVENANCE = {js_json(provenance)};\n"
        f"window.DOCS_INDEX_MODULE_CATALOGUE = {js_json(modules)};\n"
        "</script>"
    )


def render_owner_source_renderer() -> str:
    return r"""function renderOwnerSourceTable(){
  const rows = window.DOCS_INDEX_MODULE_CATALOGUE || [];
  const el = document.getElementById('ownerSourceTable');
  if(!el) return;
  const supportRows = REFS.filter(r=>['runtime governance','diagnostic','TTP/operator','schema'].includes(r.layer)).slice(0,80);
  el.innerHTML = `<h3>Live module catalogue</h3><p class="subtle">Generated from <code>atomics/skill/references/diagnostics/module-catalogue.json</code>; paths resolve to tracked atomics source, while the root <code>skill/</code> directory remains ignored runtime output.</p><div class="provenanceTableWrap provenanceTableWrap--wide ownerSourceTableWrap"><table data-owner-source="atomics/skill/references/diagnostics/module-catalogue.json" data-surface-role="raw-source"><thead><tr><th>Module ID</th><th>Class</th><th>Compiled path</th><th>Tracked source</th></tr></thead><tbody>${rows.map(r=>`<tr data-module-id="${esc(r.id)}"><td><code>${esc(r.id)}</code></td><td>${esc(r.module_class)}</td><td><code>${esc(r.path)}</code></td><td><code>${esc(r.source_path)}</code></td></tr>`).join('')}</tbody></table></div><h3>Complement-bearing source rows</h3><p class="subtle">Curated support map retained from the index source for governance/schema/source navigation. It is not the module-catalogue owner.</p><div class="provenanceTableWrap provenanceTableWrap--wide ownerSourceTableWrap"><table data-surface-role="provenance"><thead><tr><th>Path</th><th>Layer</th><th>Governs</th><th>Concepts</th><th>Operators</th></tr></thead><tbody>${supportRows.map(r=>`<tr><td><code>${esc(r.path)}</code></td><td>${esc(r.layer)}</td><td>${esc(r.governs)}</td><td>${(r.concepts||[]).map(esc).join(', ')}</td><td>${(r.operators||[]).map(esc).join(', ')}</td></tr>`).join('')}</tbody></table></div>`;
}"""


def build_index(manifest: dict[str, Any]) -> str:
    template_path = ROOT / manifest["template"]
    if not template_path.exists():
        raise SystemExit(f"{rel(template_path)}: missing template")
    modules = load_modules(manifest)
    arch = load_runtime_architecture(manifest)
    design = read_design_system()
    release_download = read_release_download_metadata(manifest)
    output = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{ GENERATED_BANNER }}": BANNER,
        "{{ DESIGN_TOKENS_CSS }}": render_design_tokens_css(design),
        "{{ TOPBAR }}": render_tabs(manifest["tabs"], release_download),
        "{{ SECTIONS }}": render_sections(manifest["tabs"], arch),
        "{{ GENERATED_DATA }}": render_generated_data(manifest, modules),
        "{{ OWNER_SOURCE_RENDERER }}": render_owner_source_renderer(),
        "{{ REFERENCE_DATA }}": render_reference_data(modules),
    }
    for token, value in replacements.items():
        if token not in output:
            raise SystemExit(f"{rel(template_path)}: missing template token {token}")
        output = output.replace(token, value)
    unresolved = [
        token
        for token in (
            "{{ GENERATED_BANNER }}",
            "{{ DESIGN_TOKENS_CSS }}",
            "{{ TOPBAR }}",
            "{{ SECTIONS }}",
            "{{ GENERATED_DATA }}",
            "{{ OWNER_SOURCE_RENDERER }}",
            "{{ REFERENCE_DATA }}",
        )
        if token in output
    ]
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
        f"window.DOCS_PIPELINE_PROVENANCE = {js_json(provenance)};\n"
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
