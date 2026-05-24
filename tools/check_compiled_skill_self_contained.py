#!/usr/bin/env python3
"""Check that the compiled skill runtime surface is self-contained."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from compiled_runtime_lib import fail_with_errors, repo_root
from package_shape import package_file_paths


RUNTIME_TEXT_SUFFIXES = {".md"}

BAD_MODEL_INSTRUCTION_PATTERNS = (
    re.compile(r"\bGENERATED FILE\b", re.IGNORECASE),
    re.compile(r"\bDo not edit directly\b", re.IGNORECASE),
    re.compile(r"\bRegenerate with tools/build_compiled_runtime\.py\b", re.IGNORECASE),
    re.compile(r"\bCanonical atomized source lives under\b", re.IGNORECASE),
)

RUNTIME_DANGLING_PATTERNS = (
    ("atomics source path", re.compile(r"atomics[\\/]", re.IGNORECASE)),
    ("expansion source path", re.compile(r"expansion[\\/]", re.IGNORECASE)),
    ("absolute Windows path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\")),
)

PATH_TOKEN_RE = re.compile(
    r"`(?P<code>[^`]*(?:/|\\)[^`]*)`|"
    r"(?P<bare>(?:skill/)?(?:README\.md|compiled-module-map\.json|build-manifest\.json|"
    r"references/[A-Za-z0-9_.\-/\\]+\.(?:md|json|ya?ml)))"
)


def normalize_rel(raw: str) -> str | None:
    token = raw.strip().strip(".,;:()[]{}\"'")
    if (
        not token
        or " " in token
        or "<" in token
        or ">" in token
        or "*" in token
        or "..." in token
        or "[" in token
        or "]" in token
    ):
        return None
    if token.startswith(("http://", "https://")):
        return None
    token = token.replace("\\", "/")
    if token.startswith("/"):
        return None
    if token.endswith("/"):
        return None
    if token.startswith("skill/"):
        token = token[len("skill/"):]
    if token in {"README.md", "compiled-module-map.json", "build-manifest.json"}:
        return token
    if token.startswith("references/"):
        return token
    return None


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def runtime_files_from_generated(root: Path) -> tuple[dict[str, str], set[str], dict[str, str], list[str]]:
    errors: list[str] = []
    paths, path_errors = package_file_paths(root)
    errors.extend(path_errors)
    texts: dict[str, str] = {}
    available: set[str] = set()
    for path in paths:
        rel = path.relative_to(root / "skill").as_posix()
        available.add(rel)
        if path.suffix.lower() in RUNTIME_TEXT_SUFFIXES:
            texts[rel] = path.read_text(encoding="utf-8")

    module_map: dict[str, str] = {}
    map_path = root / "skill" / "compiled-module-map.json"
    if map_path.is_file():
        try:
            payload = json.loads(map_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"skill/compiled-module-map.json JSON parse error: {exc}")
        else:
            module_map = canonical_paths_from_compiled_map(payload)
    else:
        errors.append("skill/compiled-module-map.json is absent")
    return texts, available, module_map, errors


def canonical_paths_from_compiled_map(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    modules = payload.get("modules")
    if not isinstance(modules, dict):
        return {}
    paths: dict[str, str] = {}
    for entry in modules.values():
        if not isinstance(entry, dict):
            continue
        canonical = entry.get("canonical_path")
        bundle = entry.get("bundle_path")
        if isinstance(canonical, str) and isinstance(bundle, str):
            rel = canonical.replace("\\", "/")
            if rel.startswith("skill/"):
                rel = rel[len("skill/"):]
            paths[rel] = bundle
    return paths


def runtime_files_from_package(path: Path) -> tuple[dict[str, str], set[str], dict[str, str], list[str]]:
    errors: list[str] = []
    texts: dict[str, str] = {}
    available: set[str] = set()
    try:
        with ZipFile(path) as zf:
            names = {name for name in zf.namelist() if name and not name.endswith("/")}
            available = set(names)
            for name in sorted(names):
                if Path(name).suffix.lower() in RUNTIME_TEXT_SUFFIXES:
                    try:
                        texts[name] = zf.read(name).decode("utf-8")
                    except UnicodeDecodeError:
                        errors.append(f"{path}: {name}: runtime text is not UTF-8")
            try:
                module_payload = json.loads(zf.read("compiled-module-map.json").decode("utf-8"))
            except KeyError:
                errors.append(f"{path}: compiled-module-map.json is absent")
                module_map = {}
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: compiled-module-map.json JSON parse error: {exc}")
                module_map = {}
            else:
                module_map = canonical_paths_from_compiled_map(module_payload)
    except BadZipFile:
        errors.append(f"{path}: package is not a readable zip payload")
        module_map = {}
    return texts, available, module_map, errors


def validate_runtime_texts(
    label: str,
    texts: dict[str, str],
    available: set[str],
    module_map: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    for rel, text in sorted(texts.items()):
        for pattern in BAD_MODEL_INSTRUCTION_PATTERNS:
            match = pattern.search(text)
            if match:
                errors.append(
                    f"{label}:{rel}:{line_number(text, match.start())}: "
                    f"BAD_MODEL_INSTRUCTION: {match.group(0)!r}"
                )
        for kind, pattern in RUNTIME_DANGLING_PATTERNS:
            match = pattern.search(text)
            if match:
                errors.append(
                    f"{label}:{rel}:{line_number(text, match.start())}: "
                    f"RUNTIME_DANGLING: {kind}: {match.group(0)!r}"
                )
        for match in PATH_TOKEN_RE.finditer(text):
            raw = match.group("code") or match.group("bare") or ""
            normalized = normalize_rel(raw)
            if not normalized:
                continue
            if normalized in available:
                continue
            if normalized in module_map and module_map[normalized] in available:
                continue
            errors.append(
                f"{label}:{rel}:{line_number(text, match.start())}: "
                f"RUNTIME_DANGLING: referenced runtime path is not packaged/resolvable: {raw!r}"
            )
    return errors


def check_generated(root: Path) -> list[str]:
    texts, available, module_map, errors = runtime_files_from_generated(root)
    if not errors:
        errors.extend(validate_runtime_texts("skill", texts, available, module_map))
    return errors


def check_package(path: Path) -> list[str]:
    texts, available, module_map, errors = runtime_files_from_package(path)
    if not errors:
        errors.extend(validate_runtime_texts(str(path), texts, available, module_map))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        action="append",
        type=Path,
        default=[],
        help="Optional .skill/.skill.zip artifact to inspect.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    errors = check_generated(root)
    for package in args.package:
        package_path = package if package.is_absolute() else root / package
        errors.extend(check_package(package_path))

    if errors:
        return fail_with_errors("compiled skill self-contained", errors)
    print("compiled skill self-contained: PASS")
    print("- generated skill runtime: checked")
    if args.package:
        for package in args.package:
            print(f"- package: {package}")
    else:
        print("- package: not checked (pass --package to inspect an artifact)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
