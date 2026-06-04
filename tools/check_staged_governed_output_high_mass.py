#!/usr/bin/env python3
"""No-model high-mass staged assembly canaries.

This checker proves assembly size floors and hash stability without committing
large output fixtures or making model/proof/release claims.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from build_staged_governed_output import assemble_manifest, manifest_for_sections, sha256_file, small_sections


ROOT = Path(__file__).resolve().parents[1]


def high_mass_sections(size_kb: int) -> list[tuple[str, str, str]]:
    filler = (
        "Synthetic high-mass no-model body prose. It is byte-budget filler only, "
        "not semantic proof, not model behavior, not release provenance, and not a sidecar claim. "
        "It preserves the single visible ACT row and does not introduce extra body_ref tokens.\n"
    )
    repeats = max(1, (size_kb * 1024) // len(filler.encode("utf-8")) + 4)
    sections = small_sections(
        act_text=(
            "## Layer B - Bounded Governed Response\n"
            "## Burden 1 / ¹B - synthetic high-mass assembly canary\n"
            "⟦ACT ¹B₁[source-status-repair.source-order] :: π=synthetic-high-mass-source-order :: "
            "body_ref=¹B₁ :: Δ=Δ¹B:source-function-bounded :: Land(¹B)+⟧\n\n"
            "#### Layer B - Governed Operation Body\n"
            "##### ¹B₁[source-status-repair] - synthetic source-order canary\n"
            "Target: source-order assembly pressure.\n"
            "Operation: keep the owner/body_ref surface stable while the section becomes large.\n"
            "Result/state-change: source-function-bounded.\n"
            "Contribution-to-Land(¹B): the only ACT submove remains parser-stable.\n\n"
            + filler * repeats
            + "\nLand(¹B): synthetic source-order burden landed for assembly stress only.\n"
        )
    )
    return sections


def canonical_without_hash_path(record: dict[str, Any]) -> str:
    clone = json.loads(json.dumps(record, sort_keys=True))
    hash_record = clone.get("hash_record")
    if isinstance(hash_record, dict):
        hash_record["sha256"] = "<self>"
    return json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def check_size(size_kb: int) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"daee-high-mass-{size_kb}kb-") as raw_tmp:
        root = Path(raw_tmp)
        case_dir = root / f"case-{size_kb}kb"
        manifest = manifest_for_sections(
            case_dir,
            case_id=f"high-mass-{size_kb}kb",
            source_input=f"high-mass-{size_kb}kb/input.md",
            section_specs=high_mass_sections(size_kb),
            target_output_kb=size_kb,
        )
        first = assemble_manifest(manifest, root=root)
        output = case_dir / "output.md"
        first_hash = sha256_file(output)
        first_record_text = canonical_without_hash_path(first)
        second = assemble_manifest(manifest, root=root)
        second_hash = sha256_file(output)
        second_record_text = canonical_without_hash_path(second)
        bytes_written = int(second.get("output", {}).get("bytes") or 0)
        if bytes_written < size_kb * 1024:
            errors.append(f"{size_kb}KB: assembled output under target: {bytes_written}")
        if first_hash != second_hash:
            errors.append(f"{size_kb}KB: output SHA changed across repeated assembly")
        if first_record_text != second_record_text:
            errors.append(f"{size_kb}KB: normalized assembly hash record changed across repeated assembly")
        non_claims = second.get("non_claims")
        if not isinstance(non_claims, dict) or not all(non_claims.values()):
            errors.append(f"{size_kb}KB: required non-claims missing from assembly hash record")
        output_text = output.read_text(encoding="utf-8")
        forbidden = ("OWNER_CONDITIONAL_RELEASE_APPROVAL_ACTIVATED", "GitHub Release", "provenance published")
        for token in forbidden:
            if token in output_text:
                errors.append(f"{size_kb}KB: forbidden release/provenance token leaked: {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 150, 200])
    args = parser.parse_args()

    errors: list[str] = []
    for size in args.sizes:
        if size <= 0:
            errors.append(f"invalid size {size}: must be positive")
            continue
        errors.extend(check_size(size))
    if errors:
        print("high-mass staged governed output check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("high-mass staged governed output check: PASS")
    print("Sizes checked: " + ", ".join(f"{size}KB" for size in args.sizes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
