#!/usr/bin/env python3
"""Build a .skill.zip payload from generated skill/ manifest entries."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from compiled_runtime_lib import fail_with_errors, repo_root
from package_shape import (
    DEFAULT_PACKAGE_PROFILE,
    PACKAGE_PROFILES,
    extra_root_file_paths,
    package_file_paths,
    profile_archive_name,
    validate_archive_names,
    validate_skill_tree,
)


SKILL_DESCRIPTION_LIMIT = 1024


def skill_description_length(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        raise ValueError("skill/SKILL.md missing YAML front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("skill/SKILL.md has malformed YAML front matter")
    lines = parts[1].splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            collected = []
            for continuation in lines[idx + 1:]:
                if continuation.startswith((" ", "\t")):
                    collected.append(continuation.strip())
                    continue
                if continuation.strip():
                    break
            return len(" ".join(collected).strip()) + 1
        return len(value.strip().strip('"\''))
    raise ValueError("skill/SKILL.md missing description metadata")


def build_archive(root: Path, output: Path, profile: str = DEFAULT_PACKAGE_PROFILE) -> tuple[int, str]:
    if profile not in PACKAGE_PROFILES:
        raise RuntimeError(f"unknown package profile: {profile!r}")

    errors = validate_skill_tree(root)
    paths, path_errors = package_file_paths(root)
    errors.extend(path_errors)
    try:
        description_len = skill_description_length(root / "skill" / "SKILL.md")
    except ValueError as exc:
        errors.append(str(exc))
        description_len = 0
    if description_len > SKILL_DESCRIPTION_LIMIT:
        errors.append(
            f"skill/SKILL.md description is {description_len} characters; "
            f"maximum is {SKILL_DESCRIPTION_LIMIT}"
        )

    extra_paths, extra_errors = extra_root_file_paths(root, profile)
    errors.extend(extra_errors)

    if errors:
        raise RuntimeError("\n".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    skill = root / "skill"
    with ZipFile(output, "w", ZIP_DEFLATED) as zf:
        for path in paths:
            rel = path.relative_to(skill).as_posix()
            info = ZipInfo(rel)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(info, path.read_bytes())
        for path in extra_paths:
            rel = path.relative_to(root).as_posix()
            info = ZipInfo(rel)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(info, path.read_bytes())

    with ZipFile(output) as zf:
        names = zf.namelist()
    archive_errors = validate_archive_names(names, profile=profile)
    if archive_errors:
        output.unlink(missing_ok=True)
        raise RuntimeError("\n".join(archive_errors))
    digest = hashlib.sha256(output.read_bytes()).hexdigest().upper()
    return len(names), digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help=(
            "Output .skill.zip path. Optional when --version is given; in that "
            "case the canonical profile-suffixed name "
            "(daee-epistemics-<version>-<profile>.skill.zip) is used, written "
            "under --output-dir (default: build/)."
        ),
    )
    parser.add_argument(
        "--profile",
        choices=PACKAGE_PROFILES,
        default=DEFAULT_PACKAGE_PROFILE,
        help=(
            "Package profile to build. execution-mini (default) is the "
            "canonical compiled-runtime-only package. audit-full additionally "
            "packages schema/, tools/, tests/, and docs/ for build/test audit "
            "and is explicitly non-default."
        ),
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Release-line version (e.g. v0.4.6.0) used to derive the canonical output name when 'output' is omitted.",
    )
    parser.add_argument(
        "--output-dir",
        default="build",
        help="Directory for the derived canonical output name when 'output' is omitted (default: build).",
    )
    parser.add_argument(
        "--legacy-name",
        action="store_true",
        help=(
            "Accept/emit the pre-profile archive name (daee-epistemics-<version>.skill.zip, "
            "no profile suffix) when deriving the output path from --version. Only affects "
            "the derived-name path; an explicit 'output' argument is always used as-is."
        ),
    )
    args = parser.parse_args(argv)

    root = repo_root()

    if args.output is None:
        if not args.version:
            return fail_with_errors(
                "package skill",
                ["either an explicit output path or --version must be supplied"],
            )
        if args.legacy_name:
            name = f"daee-epistemics-{args.version}.skill.zip"
        else:
            name = profile_archive_name(args.version, args.profile)
        output = Path(args.output_dir) / name
    else:
        output = Path(args.output)

    if output.suffix.lower() != ".zip" or not output.name.lower().endswith(".skill.zip"):
        return fail_with_errors(
            "package skill",
            ["output name must end with .skill.zip"],
        )
    if not output.is_absolute():
        output = root / output
    try:
        entries, digest = build_archive(root, output, profile=args.profile)
    except RuntimeError as exc:
        return fail_with_errors("package skill", str(exc).splitlines())

    print(f"Archive: {output}")
    print(f"Profile: {args.profile}")
    print(f"Entries: {entries}")
    print("Root check: PASS")
    print("Separator check: PASS")
    print("Compiled metadata check: PASS")
    print(f"SHA256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
