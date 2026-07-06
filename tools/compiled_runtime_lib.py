#!/usr/bin/env python3
"""Shared helpers for the compiled runtime compiler/checkers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPILER_VERSION = "0.3.2"
BUNDLE_MAPPING_VERSION = "2026-04-28.phase5"
SOURCE_ROOT_REL = "atomics/skill"
OUTPUT_ROOT_REL = "skill"
LEGACY_SOURCE_ROOT_REL = "skill"

GENERATED_WARNING = (
    "GENERATED FILE. Do not edit directly. Canonical atomized source lives under "
    "atomics/skill/. Regenerate with tools/build_compiled_runtime.py."
)

SECTION_FIELDS = ("MODULE_ID", "MODULE_CLASS", "CANONICAL_PATH", "SOURCE_SHA256")


@dataclass(frozen=True)
class SourceDoc:
    path: Path
    rel_path: str
    text: str
    frontmatter: dict[str, Any]
    body: str
    sha256: str

    @property
    def module_id(self) -> str:
        return str(self.frontmatter.get("id", ""))

    @property
    def module_class(self) -> str:
        return str(self.frontmatter.get("module_class", ""))

    @property
    def canonical_path(self) -> str:
        return str(self.frontmatter.get("canonical_path", ""))

    @property
    def source_rel_path(self) -> str:
        return self.rel_path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root(root: Path) -> Path:
    return root / SOURCE_ROOT_REL


def source_rel_from_legacy(path: str) -> str:
    normalized = path.replace("\\", "/")
    for prefix in (f"{SOURCE_ROOT_REL}/", f"{LEGACY_SOURCE_ROOT_REL}/"):
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized


def canonical_source_rel(path: str) -> str:
    return f"{SOURCE_ROOT_REL}/{source_rel_from_legacy(path)}"


def source_path_for(root: Path, path: str) -> Path:
    return source_root(root) / source_rel_from_legacy(path)


def posix_rel(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    return os.path.relpath(path, base).replace("\\", "/")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_runtime_surface_text(text: str) -> str:
    """Remove source-tree-only wording from model-readable compiled runtime text."""
    replacements = {
        "atomics/skill/** tracked in repo as canonical source": (
            "source files tracked in repo as canonical build inputs"
        ),
        "skill/** ignored local/CI generated runtime output": (
            "compiled skill files are ignored local/CI runtime output"
        ),
        "CI/local build compiles atomics -> generated skill/**": (
            "CI/local build compiles source inputs into the generated skill runtime"
        ),
        "raw atomics are not distributed as the .skill runtime": (
            "raw source tree is not distributed as the .skill runtime"
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"atomics/skill/[A-Za-z0-9_.\-/]+", "compiled runtime module metadata", text)
    text = text.replace("atomics/skill/", "compiled runtime module metadata")
    return text


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, str]:
    if not text.startswith("---"):
        raise ValueError("missing YAML front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed YAML front matter")
    raw = parts[1].strip("\r\n")
    body = parts[2].lstrip("\r\n")
    return parse_simple_yaml(raw), raw, body


def parse_simple_yaml(raw: str) -> dict[str, Any]:
    """Parse the small YAML subset used by operative contract front matter.

    This intentionally avoids a PyYAML dependency so the phase-2 tools run in
    stripped-down Python environments. It supports top-level scalars and
    top-level lists of scalar strings, plus folded/literal block scalars used
    by skill metadata descriptions.
    """
    data: dict[str, Any] = {}
    current_key: str | None = None
    block_key: str | None = None
    block_style = ""
    block_lines: list[str] = []

    def flush_block() -> None:
        nonlocal block_key, block_style, block_lines
        if block_key is None:
            return
        if block_style.startswith(">"):
            data[block_key] = " ".join(line.strip() for line in block_lines if line.strip())
        else:
            data[block_key] = "\n".join(line.rstrip() for line in block_lines)
        block_key = None
        block_style = ""
        block_lines = []

    for raw_line in raw.splitlines():
        if block_key is not None:
            if not raw_line.strip() or raw_line[:1].isspace():
                block_lines.append(raw_line.strip())
                continue
            flush_block()
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, [])
            if not isinstance(data[current_key], list):
                raise ValueError(f"YAML key {current_key!r} mixes scalar and list values")
            data[current_key].append(_parse_scalar(stripped[2:].strip()))
            continue
        if line[:1].isspace():
            raise ValueError(f"unsupported indented YAML shape: {line!r}")
        if ":" not in line:
            raise ValueError(f"unsupported YAML line: {line!r}")
        key, value = line.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if value in {">", ">-", "|", "|-"}:
            block_key = current_key
            block_style = value
            block_lines = []
        elif value == "":
            data[current_key] = []
        else:
            data[current_key] = _parse_scalar(value)
    flush_block()
    return data


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "~"}:
        return None
    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    return value


def load_source_doc(root: Path, rel_path: str) -> SourceDoc:
    path = source_path_for(root, rel_path)
    text = read_text(path)
    frontmatter, _raw, body = parse_frontmatter(text)
    sha = sha256_file(path)
    return SourceDoc(
        path=path,
        rel_path=canonical_source_rel(rel_path),
        text=text,
        frontmatter=frontmatter,
        body=body,
        sha256=sha,
    )


def load_catalogue(root: Path) -> list[dict[str, str]]:
    path = source_path_for(root, "skill/references/diagnostics/module-catalogue.json")
    payload = json.loads(read_text(path))
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ValueError("module-catalogue.json must contain a top-level modules list")
    return modules


def catalogue_by_id(root: Path) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for entry in load_catalogue(root):
        module_id = entry.get("id")
        if not isinstance(module_id, str):
            raise ValueError(f"catalogue entry is missing id: {entry!r}")
        if module_id in by_id:
            raise ValueError(f"duplicate catalogue id: {module_id}")
        by_id[module_id] = entry
    return by_id


BUNDLE_SOURCES: dict[str, list[str]] = {
    "references/runtime-foundation.md": [
        "skill/references/terminology.md",
        "skill/references/case-library/INDEX.md",
        "skill/references/module-codes.md",
        "skill/references/techniques/heuristics.md",
    ],
    "references/runtime-diagnostic-core.md": [
        "skill/references/techniques/V1-diagnostic.md",
        "skill/references/diagnostics/noetic-reading-checklist.md",
        "skill/references/diagnostics/seven-deformations.md",
        "skill/references/diagnostics/modes-of-concealment.md",
        "skill/references/diagnostics/discourse-orientation.md",
        "skill/references/tactics/M5-deformation-triage.md",
    ],
    "references/runtime-phase2-passes.md": [
        "skill/references/diagnostics/reason-disambiguation.md",
        "skill/references/diagnostics/foreign-premise-detection.md",
        "skill/references/diagnostics/prophetic-discourse-neutralization.md",
        "skill/references/diagnostics/arabic-backbone-predicates.md",
    ],
    "references/runtime-dispatch-gate.md": [
        "skill/references/diagnostics/diagnostic-ir.md",
        "skill/references/diagnostics/ir-reconstruction-pass.md",
        "skill/references/diagnostics/case-state-schema.md",
        "skill/references/diagnostics/pattern-profiling.md",
        "skill/references/diagnostics/inference-boundary.md",
        "skill/references/diagnostics/mixed-case-handling.md",
        "skill/references/diagnostics/anti-patterns.md",
        "skill/references/diagnostics/framework-pipeline.md",
        "skill/references/diagnostics/recursive-state-transitions.md",
        "skill/references/diagnostics/routing-precedence.md",
        "skill/references/kernel-thesis.md",
        "skill/references/metaphysical-architecture.md",
        "skill/references/procedures/P7-restoration-stops.md",
    ],
    "references/runtime-output-governance.md": [
        "skill/references/rubrics/output-release.md",
        "skill/references/rubrics/diagnostic-render-contract.md",
    ],
    "references/omnibus/OMNIBUS-profiles.md": [
        "skill/references/case-library/profiles/INDEX.md",
        "skill/references/case-library/noetic-profiles.md",
        "skill/references/case-library/profiles/ns-1-naturalist.md",
        "skill/references/case-library/profiles/ns-2-agnostic-evidentialist.md",
        "skill/references/case-library/profiles/ns-3-deconverted.md",
        "skill/references/case-library/profiles/ns-4-secular-moral-realist.md",
        "skill/references/case-library/profiles/ns-5-habituated-atheist.md",
        "skill/references/case-library/profiles/ns-6-kalamic-evidentialist.md",
        "skill/references/case-library/profiles/ns-7-theistic-evidentialist.md",
        "skill/references/case-library/profiles/ns-8-muslim-internal-crisis.md",
        "skill/references/case-library/profiles/ns-9-historical-critical-skeptic.md",
        "skill/references/case-library/profiles/ns-10-maturidi-evidentialist.md",
        "skill/references/case-library/profiles/ns-11-fideist-reformed.md",
        "skill/references/case-library/profiles/ns-12-blank-slate-dual-fitrah.md",
    ],
    "references/omnibus/OMNIBUS-do-families.md": [
        "skill/references/case-library/do-core.md",
        "skill/references/case-library/do-second-loop.md",
        "skill/references/case-library/do-christian-extensions.md",
        "skill/references/case-library/do-attribute-precision.md",
        "skill/references/case-library/philosophical-usurpation.md",
        "skill/references/sound-reason-epistemology.md",
        "skill/references/prophecy-wahy-supremacy.md",
    ],
    "references/omnibus/OMNIBUS-rt-transmission.md": [
        "skill/references/case-library/revelation-transmission.md",
        "skill/references/techniques/V10-transmission-content-vetting.md",
    ],
    "references/omnibus/OMNIBUS-tactics.md": [
        "skill/references/tactics/INDEX.md",
        "skill/references/tactics/E1-broadening-evidence.md",
        "skill/references/tactics/E2-inferential-criterion.md",
        "skill/references/tactics/E3-cumulative-case.md",
        "skill/references/tactics/E4-cross-cultural-check.md",
        "skill/references/tactics/F1-supra-vs-antirational.md",
        "skill/references/tactics/F2-volitional-dimensions.md",
        "skill/references/tactics/F3-practice-epistemic-access.md",
        "skill/references/tactics/R1-internalist-criterion.md",
        "skill/references/tactics/R2-the-reminder.md",
        "skill/references/tactics/R3-warranted-basic-belief.md",
        "skill/references/tactics/TTP-MRP-mid-reread-pressure.md",
        "skill/references/tactics/M1-self-refutation.md",
        "skill/references/tactics/M1P-performative-self-refutation.md",
        "skill/references/tactics/M2-prior-probability.md",
        "skill/references/tactics/M3-orphaned-intuition.md",
        "skill/references/tactics/M4-grief-register.md",
        "skill/references/tactics/M6-excluded-middle.md",
        "skill/references/tactics/M7-definition-anchor.md",
        "skill/references/tactics/M8-reductio.md",
        "skill/references/tactics/M9-predication-mode.md",
        "skill/references/tactics/doubt-vs-skepticism.md",
        "skill/references/tactics/husn-al-nazar-arguments.md",
        "skill/references/tactics/inductive-fitri-method.md",
        "skill/references/tactics/symmetric-taqlid-check.md",
    ],
    "references/omnibus/OMNIBUS-techniques.md": [
        "skill/references/techniques/INDEX.md",
        "skill/references/techniques/V2-reconstituting-reason.md",
        "skill/references/techniques/V3-regress-dissolution.md",
        "skill/references/techniques/V4-contamination-identification.md",
        "skill/references/techniques/V5-directing-attention-signs.md",
        "skill/references/techniques/V6-convergence.md",
        "skill/references/techniques/V7-taqlid-check.md",
        "skill/references/techniques/V8-bila-kayf-anchor.md",
        "skill/references/techniques/V9-necessary-knowledge-priority.md",
        "skill/references/techniques/V11-taqlid-transition.md",
        "skill/references/techniques/V12-tamanuc-exhaustion.md",
    ],
    "references/omnibus/OMNIBUS-procedures.md": [
        "skill/references/procedures/INDEX.md",
        "skill/references/procedures/P1-fitrah-restoration.md",
        "skill/references/procedures/P2-objection-mapping.md",
        "skill/references/procedures/P3-reason-revelation-tension.md",
        "skill/references/procedures/P4-maieutic.md",
        "skill/references/procedures/P5-already-believing.md",
        "skill/references/procedures/P6-universal-aqidah-principle.md",
    ],
    "references/omnibus/OMNIBUS-specialty-diagnostics.md": [
        "skill/references/diagnostics/INDEX.md",
        "skill/references/diagnostics/kalamic-interlocutor.md",
        "skill/references/diagnostics/fitrah-perspectives.md",
        "skill/references/diagnostics/hadith-authentication-epistemology.md",
        "skill/references/diagnostics/causal-series-taxonomy.md",
        "skill/references/diagnostics/definition-discipline.md",
        "skill/references/diagnostics/nomenclature-normalization.md",
        "skill/references/diagnostics/proof-method-audit.md",
        "skill/references/diagnostics/perfection-criterion-usurpation.md",
    ],
}


EXTRA_INPUTS = [
    "skill/SKILL.md",
    "skill/references/rubrics/non-droppable-manual-contract.md",
    "skill/references/rubrics/manual-contract-digest.md",
    "skill/references/diagnostics/framework-pipeline.yaml",
    "skill/references/diagnostics/module-catalogue.json",
    "skill/references/diagnostics/delta-result-vocabulary.json",
    "skill/references/diagnostics/diagnostic-ir.schema.json",
    "skill/references/diagnostics/operative-contract.schema.json",
]

RUNTIME_METADATA_COPIES = [
    "skill/README.md",
    "skill/references/rubrics/non-droppable-manual-contract.md",
    "skill/data/module-catalogue.json",
    "skill/data/ontology-licenses.yaml",
    "skill/data/routing-precedence.yaml",
    "skill/data/trigger-matrix.json",
    "skill/references/diagnostics/module-catalogue.json",
    "skill/references/diagnostics/delta-result-vocabulary.json",
    "skill/references/diagnostics/diagnostic-ir.schema.json",
    "skill/references/diagnostics/operative-contracts.md",
    "skill/references/diagnostics/operative-contract.schema.json",
    "skill/scripts/check_execution.py",
    "skill/scripts/daee_level3.py",
    "skill/scripts/diagnose.py",
    "skill/scripts/level3_lib.py",
    "skill/scripts/reconstruct.py",
    "skill/scripts/route.py",
    "skill/scripts/validate.py",
    "skill/tests/expected/genuine-shubhah-after-deformation-clearing.json",
    "skill/tests/expected/grief-coded-objection.json",
    "skill/tests/expected/imported-tribunal-protest.json",
    "skill/tests/expected/mushabara-fasida.json",
    "skill/tests/expected/naturalist-evidential-tribunal.json",
    "skill/tests/expected/stability-repetition.json",
    "skill/tests/expected/trinitarian-claim-cluster.json",
    "skill/tests/expected/moral-protest-nonbelief-worship-worthiness.json",
    "skill/tests/fixtures/genuine-shubhah-after-deformation-clearing/input.md",
    "skill/tests/fixtures/grief-coded-objection/input.md",
    "skill/tests/fixtures/imported-tribunal-protest/input.md",
    "skill/tests/fixtures/mushabara-fasida/input.md",
    "skill/tests/fixtures/naturalist-evidential-tribunal/input.md",
    "skill/tests/fixtures/stability-repetition/input.md",
    "skill/tests/fixtures/trinitarian-claim-cluster/input.md",
    "skill/tests/fixtures/moral-protest-nonbelief-worship-worthiness/input.md",
]


def all_bundle_sources() -> list[str]:
    paths: list[str] = []
    for bundle_sources in BUNDLE_SOURCES.values():
        paths.extend(bundle_sources)
    return paths


def out_dir(root: Path) -> Path:
    return root / OUTPUT_ROOT_REL


def _rmtree_resilient(path: Path) -> list[Path]:
    """Remove a directory tree, tolerating filesystems that reject unlink (e.g. virtiofs).

    On virtiofs mounts, os.unlink raises PermissionError even for files the process owns.
    We detect this and fall back to truncating files in place so the build can overwrite them.
    Any remaining files are returned so release/check builds fail instead of silently
    carrying stale output.
    """
    def _onerror(func, fpath, _excinfo):  # noqa: ANN001
        pass  # ignore errors in rmtree so we can fall through to truncation pass

    try:
        shutil.rmtree(path, onerror=_onerror)
    except Exception:  # noqa: BLE001
        pass

    # Truncation pass: any file that still exists gets zeroed, then unlinked
    # again. Some Windows/virtiofs combinations reject the first rmtree unlink
    # but allow removal after the handle has been rewritten.
    if path.exists():
        for child in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if child.is_file():
                try:
                    child.write_bytes(b"")
                except (PermissionError, OSError):
                    pass
                try:
                    child.unlink()
                except (PermissionError, OSError):
                    pass
            elif child.is_dir():
                try:
                    child.rmdir()
                except (PermissionError, OSError):
                    pass
        try:
            path.rmdir()
        except (PermissionError, OSError):
            pass
    if not path.exists():
        return []
    return sorted(child for child in path.rglob("*") if child.is_file())


GENERATED_SKILL_SENTINELS = (
    "# NON-DROPPABLE DEFAULT MANUAL CONTRACT",
    "When this compiled SKILL.md is the supplied runtime surface",
    "The generated bundle map is `compiled-module-map.json`.",
)


def is_generated_skill_surface(path: Path) -> bool:
    """Return true for generated SKILL.md outputs, including legacy single-file checkouts."""
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "GENERATED FILE." in text:
        return True
    return all(sentinel in text for sentinel in GENERATED_SKILL_SENTINELS)


def clean_compiled_dir(root: Path) -> Path:
    target = out_dir(root).resolve()
    expected = (root / OUTPUT_ROOT_REL).resolve()
    if target != expected or target == source_root(root).resolve():
        raise RuntimeError(f"refusing to clean unexpected path: {target}")
    if target.exists():
        marker = target / "SKILL.md"
        manifest = target / "build-manifest.json"
        has_generated_marker = is_generated_skill_surface(marker)
        has_generated_manifest = (
            manifest.is_file()
            and '"generated": true' in manifest.read_text(encoding="utf-8", errors="ignore")
        )
        if marker.is_file() and not (has_generated_marker or has_generated_manifest):
            raise RuntimeError(f"refusing to clean non-generated runtime root: {target}")
        leftovers = _rmtree_resilient(target)
        if leftovers:
            rels = ", ".join(str(path.relative_to(target)).replace("\\", "/") for path in leftovers[:20])
            raise RuntimeError(f"failed to clean generated runtime root; stale file(s) remain: {rels}")
    target.mkdir(parents=True, exist_ok=True)
    return target


def build_section(doc: SourceDoc) -> str:
    title = doc.module_id or Path(doc.rel_path).name
    return (
        f"\n\n## RUNTIME MODULE: {title}\n\n"
        f"<!-- MODULE_ID: {doc.module_id} -->\n"
        f"<!-- MODULE_CLASS: {doc.module_class} -->\n"
        f"<!-- CANONICAL_PATH: {doc.canonical_path} -->\n"
        f"<!-- SOURCE_SHA256: {doc.sha256} -->\n\n"
        f"{normalize_runtime_surface_text(doc.text.rstrip())}\n\n"
        f"<!-- END_MODULE: {doc.module_id} -->\n"
    )


def parse_compiled_sections(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    section_pattern = re.compile(
        r"<!-- MODULE_ID:\s*(?P<MODULE_ID>.*?)\s*-->\s*\n"
        r"<!-- MODULE_CLASS:\s*(?P<MODULE_CLASS>.*?)\s*-->\s*\n"
        r"<!-- CANONICAL_PATH:\s*(?P<CANONICAL_PATH>.*?)\s*-->\s*\n"
        r"<!-- SOURCE_SHA256:\s*(?P<SOURCE_SHA256>[0-9a-fA-F]+)\s*-->\s*\n\n"
        r"(?P<GENERATED_BODY>.*?)\n<!-- END_MODULE:\s*(?P<END_MODULE>.*?)\s*-->",
        flags=re.DOTALL,
    )
    matches = list(section_pattern.finditer(text))
    if not matches:
        section_pattern = re.compile(
        r"<!-- SOURCE:\s*(?P<SOURCE>.*?)\s*-->\s*\n"
        r"<!-- MODULE_ID:\s*(?P<MODULE_ID>.*?)\s*-->\s*\n"
        r"<!-- MODULE_CLASS:\s*(?P<MODULE_CLASS>.*?)\s*-->\s*\n"
        r"<!-- CANONICAL_PATH:\s*(?P<CANONICAL_PATH>.*?)\s*-->\s*\n"
        r"<!-- SOURCE_SHA256:\s*(?P<SOURCE_SHA256>[0-9a-fA-F]+)\s*-->\s*\n\n"
        r"(?P<GENERATED_BODY>.*?)\n<!-- END_SOURCE:\s*(?P<END_SOURCE>.*?)\s*-->",
        flags=re.DOTALL,
        )
        matches = list(section_pattern.finditer(text))
    if matches:
        sections: list[dict[str, str]] = []
        for match in matches:
            section = match.groupdict()
            section["BUNDLE_PATH"] = posix_rel(path)
            sections.append(section)
        return sections

    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    pattern = re.compile(r"^<!--\s*([A-Z0-9_]+):\s*(.*?)\s*-->$")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if key == "SOURCE":
            if current:
                sections.append(current)
            current = {"BUNDLE_PATH": posix_rel(path)}
        if current is not None:
            current[key] = value
    if current:
        sections.append(current)
    return sections


def generated_markdown_files(root: Path) -> list[Path]:
    compiled_root = out_dir(root)
    if not compiled_root.exists():
        return []
    return sorted(path for path in compiled_root.rglob("*.md") if path.is_file())


def fail_with_errors(title: str, errors: list[str]) -> int:
    if not errors:
        print(f"{title}: PASS")
        return 0
    print(f"{title}: FAIL")
    for error in errors:
        print(f"- {error}")
    return 1
