#!/usr/bin/env python3
"""Validate operative-contract front matter for the RC2 focused owner set."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "atomics/skill/references/diagnostics/module-catalogue.json"
CONTRACT_SCHEMA = ROOT / "atomics/skill/references/diagnostics/operative-contract.schema.json"

FOCUSED_MODULES = [
    "E3-cumulative-case",
    "E4-cross-cultural-check",
    "F3-practice-epistemic-access",
    "M1P-performative-self-refutation",
    "M6-excluded-middle",
    "M7-definition-anchor",
    "R1-internalist-criterion",
    "R2-the-reminder",
    "R3-warranted-basic-belief",
    "inductive-fitri-method",
    "P2-objection-mapping",
    "P5-already-believing",
    "V3-regress-dissolution",
    "V6-convergence",
    "V1-diagnostic",
    "M1-self-refutation",
    "M9-predication-mode",
    "P7-restoration-stops",
    "definition-discipline",
]

REQUIRED_KEYS = {"id", "module_class", "canonical_path", "contract_version"}
FORBIDDEN_KEYS = {"blocked_moves", "fixture_refs"}


def parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, object] = {}
    current: str | None = None
    for line in text[: end + 4].splitlines():
        stripped = line.strip()
        if stripped == "---" or not stripped:
            continue
        if ":" in line and not stripped.startswith("- "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current = None
            else:
                data[key] = []
                current = key
            continue
        if current and stripped.startswith("- "):
            existing = data.setdefault(current, [])
            if isinstance(existing, list):
                existing.append(stripped[2:])
    return data


def owner_path(canonical_path: str) -> Path:
    if canonical_path.startswith("skill/"):
        return ROOT / "atomics/skill" / canonical_path[len("skill/") :]
    return ROOT / canonical_path


def main() -> int:
    errors: list[str] = []
    if not CONTRACT_SCHEMA.is_file():
        errors.append(f"operative contract schema is absent: {CONTRACT_SCHEMA.relative_to(ROOT).as_posix()}")
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    modules = {item["id"]: item for item in catalogue.get("modules", []) if isinstance(item, dict) and "id" in item}

    for module_id in FOCUSED_MODULES:
        entry = modules.get(module_id)
        if entry is None:
            errors.append(f"{module_id}: absent from module catalogue")
            continue
        path = owner_path(entry["path"])
        if not path.is_file():
            errors.append(f"{module_id}: owner file absent: {entry['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        missing = sorted(REQUIRED_KEYS - set(frontmatter))
        if missing:
            errors.append(f"{module_id}: front matter missing required key(s): {', '.join(missing)}")
        for key in FORBIDDEN_KEYS & set(frontmatter):
            errors.append(
                f"{module_id}: unsupported front matter key {key!r}; use existing schema keys such as 'blocks'"
            )
        if frontmatter.get("id") != module_id:
            errors.append(f"{module_id}: id mismatch: {frontmatter.get('id')!r}")
        if frontmatter.get("module_class") != entry.get("module_class"):
            errors.append(f"{module_id}: module_class mismatch: {frontmatter.get('module_class')!r}")
        if frontmatter.get("canonical_path") != entry.get("path"):
            errors.append(f"{module_id}: canonical_path mismatch: {frontmatter.get('canonical_path')!r}")
        if "load_when" not in frontmatter:
            errors.append(f"{module_id}: load_when is absent")
        if "output_shapes" not in frontmatter:
            errors.append(f"{module_id}: output_shapes is absent")
        companions = frontmatter.get("companions")
        if isinstance(companions, list):
            for companion in companions:
                if companion not in modules:
                    errors.append(f"{module_id}: companion not in catalogue: {companion}")

    if errors:
        print("operative contracts: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("operative contracts: PASS")
    print(f"- focused owners checked: {len(FOCUSED_MODULES)}")
    print("- required frontmatter keys: id, module_class, canonical_path, contract_version")
    print("- unsupported fixture_refs/blocked_moves keys absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
