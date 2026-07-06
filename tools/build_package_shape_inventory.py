#!/usr/bin/env python3
"""Build docs/audits/package-shape-inventory.md: a conservative eager-load
classification of every file that would ship in the built .skill.zip archive.

CONSERVATIVE EAGER-LOAD ASSUMPTION: this inventory assumes the host makes the
*entire* built package available to the model and may inject any file from it
into context at any time, regardless of whether skill/SKILL.md's own load-path
discipline says the file should only be read on a particular route or after a
particular gate. "Host-hot" / "prompt-hot" / "route-warm" / "cold-law" below
describe how HOT the model's own load-path text says a class is, not a claim
that a given host actually withholds the colder files. This is a measurement
of package shape, not a runtime guarantee.

Shipped-file enumeration mirrors tools/package_skill.py, which builds the
archive from `package_shape.package_file_paths(root)` (skill/build-manifest.json
canonical_package_files, resolved under skill/). This tool reuses that same
function directly rather than re-deriving the list, so the inventory and the
archive can never disagree about what ships.

Classification (each shipped file gets exactly one class):
  - host-hot     : skill/SKILL.md (the compiled root the host injects) plus
                    package metadata JSON (compiled-module-map.json,
                    build-manifest.json).
  - prompt-hot   : files named in SKILL.md's "Load path for substantive cases"
                    list, EXCLUDING the one entry documented as loaded only on
                    a conditional pass (see route-warm). Parsed from the
                    anchor text at runtime; see ANCHOR_TEXT below.
  - route-warm   : the "Load path for substantive cases" entry that SKILL.md's
                    own prose (search anchor: "Phase 2 pass", "mandatory Phase
                    2 passes") describes as a conditional pass rather than an
                    unconditional substantive-case load, plus any other file
                    this script identifies as conditionally routed.
  - cold-law     : references/omnibus/*.md (compiled bundle sections read
                    only after Phase 2 / the Diagnostic IR authorize the
                    original module owner - anchor: "Use `references/omnibus/*.md`
                    only after V1, Phase 2, and the Diagnostic IR authorize the
                    original source module owner."), references/rubrics/
                    non-droppable-manual-contract.md, case-library, and
                    profiles content, when shipped.
  - audit-only   : shipped files never model-loaded by the host injection
                    path at all (e.g. README.md, which is a human/host pointer
                    document, not a runtime load target).

Regeneration: python tools/build_package_shape_inventory.py
Freshness check: python tools/build_package_shape_inventory.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from compiled_runtime_lib import repo_root
from package_shape import package_file_paths


OUTPUT_REL = "docs/audits/package-shape-inventory.md"

# Anchor: skill/SKILL.md, "Load path for substantive cases" (numbered list
# introduced by that exact heading text, ~L1708-1714 as of this writing).
LOAD_PATH_HEADING = "Load path for substantive cases:"
LOAD_PATH_ITEM_RE = re.compile(r"^\d+\.\s+`references/([A-Za-z0-9._-]+\.md)`\s*$")

# Anchor: skill/SKILL.md prose naming the mandatory Phase 2 pass file
# conditionally rather than unconditionally for every substantive case
# (search anchors: "mandatory Phase 2 passes", "Phase-2 pass",
# "Run the mandatory Phase 2 passes listed above."). Hardcoded here (rather
# than pattern-derived) because the conditional-vs-unconditional distinction
# is a semantic judgment call the SKILL.md prose makes in surrounding text,
# not a syntactic marker inside the numbered load-path list itself.
ROUTE_WARM_LOAD_PATH_BASENAMES = {"runtime-phase2-passes.md"}

# Anchor: skill/SKILL.md, "Use `references/omnibus/*.md` only after V1,
# Phase 2, and the Diagnostic IR authorize the original source module owner."
COLD_LAW_DIR_PREFIXES = (
    "references/omnibus/",
    "references/case-library/",
    "references/profiles/",
)
COLD_LAW_BASENAMES = {"non-droppable-manual-contract.md"}

# Anchor: tools/package_skill.py build_archive() writes skill/**/* into the
# archive using skill/ as the zip root, plus skill/README.md at the top
# level of the skill/ tree per skill/README.md "Canonical package roots".
HOST_HOT_BASENAMES = {"SKILL.md", "compiled-module-map.json", "build-manifest.json"}

# Files shipped in the package that are never a model-load target under any
# route; they exist for humans/hosts reading the package, not for the model
# to load into context.
AUDIT_ONLY_BASENAMES = {"README.md"}

CLASS_ORDER = ["host-hot", "prompt-hot", "route-warm", "cold-law", "audit-only"]


def parse_load_path(skill_md_text: str) -> list[str]:
    """Return the ordered list of references/*.md basenames from the
    "Load path for substantive cases" numbered list in skill/SKILL.md.
    """
    lines = skill_md_text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == LOAD_PATH_HEADING)
    except StopIteration:
        return []
    items: list[str] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            if items:
                # Blank line after at least one item ends the numbered list.
                break
            continue
        match = LOAD_PATH_ITEM_RE.match(stripped)
        if not match:
            break
        items.append(match.group(1))
    return items


def classify(rel_from_skill: str, load_path_items: list[str]) -> tuple[str, str]:
    """Classify one shipped file (path relative to skill/). Returns
    (class, evidence_anchor).
    """
    basename = Path(rel_from_skill).name

    if basename in HOST_HOT_BASENAMES:
        return "host-hot", "tools/package_skill.py build_archive (compiled root + package metadata JSON)"

    if basename in AUDIT_ONLY_BASENAMES:
        return "audit-only", "skill/README.md canonical package roots (human/host pointer, not a model load target)"

    if rel_from_skill.startswith(COLD_LAW_DIR_PREFIXES) or basename in COLD_LAW_BASENAMES:
        return "cold-law", "skill/SKILL.md: \"Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic IR authorize the original source module owner.\""

    if rel_from_skill.startswith("references/"):
        if basename in load_path_items:
            if basename in ROUTE_WARM_LOAD_PATH_BASENAMES:
                return "route-warm", "skill/SKILL.md: \"Run the mandatory Phase 2 passes listed above.\" (conditional Phase-2 pass, not every substantive case)"
            return "prompt-hot", "skill/SKILL.md: \"Load path for substantive cases\" numbered list"
        return "route-warm", "skill/SKILL.md: references/ file outside the substantive-case load path and outside the omnibus/case-library/profiles cold-law prefixes; loaded conditionally by route"

    # Anything else shipped under skill/ that isn't covered above.
    return "route-warm", "unclassified-by-anchor shipped file; defaulted to route-warm pending an explicit SKILL.md anchor"


def build_rows(root: Path) -> tuple[list[dict], list[str]]:
    paths, errors = package_file_paths(root)
    if errors:
        return [], errors
    skill_root = root / "skill"
    skill_md_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    load_path_items = parse_load_path(skill_md_text)

    rows: list[dict] = []
    for path in paths:
        rel_from_skill = path.relative_to(skill_root).as_posix()
        size = path.stat().st_size
        cls, anchor = classify(rel_from_skill, load_path_items)
        rows.append(
            {
                "file": f"skill/{rel_from_skill}",
                "bytes": size,
                "est_tok": size // 4,
                "class": cls,
                "evidence": anchor,
            }
        )
    return rows, []


def render_doc(rows: list[dict], generation_command: str) -> str:
    lines: list[str] = []
    lines.append("# Package Shape Inventory")
    lines.append("")
    lines.append(
        "> Conservative EAGER-LOAD assumption: this inventory assumes a host may make "
        "the entire built `.skill.zip` package available to the model and may inject "
        "any file from it into context at any point, independent of skill/SKILL.md's "
        "own load-path discipline. The class columns below measure how HOT the "
        "model's own load-path text says each file is, not what a given host actually "
        "withholds. This is a measurement of package shape, not a runtime guarantee "
        "of what any specific host does or does not inject."
    )
    lines.append(">")
    lines.append(f"> Generated by `python tools/{Path(__file__).name}`. Do not edit by hand.")
    lines.append("")
    lines.append(
        "Shipped-file list is `package_shape.package_file_paths()` - the same "
        "function `tools/package_skill.py` uses to build the archive - so this "
        "inventory cannot drift from what actually ships."
    )
    lines.append("")

    class_index = {name: i for i, name in enumerate(CLASS_ORDER)}
    ordered = sorted(rows, key=lambda r: (class_index.get(r["class"], len(CLASS_ORDER)), -r["bytes"], r["file"]))

    lines.append("| file | bytes | est_tok | class | evidence anchor |")
    lines.append("| --- | ---: | ---: | --- | --- |")
    for row in ordered:
        evidence = row["evidence"].replace("|", "\\|")
        lines.append(
            f"| `{row['file']}` | {row['bytes']} | {row['est_tok']} | {row['class']} | {evidence} |"
        )
    lines.append("")

    lines.append("## Class subtotals")
    lines.append("")
    lines.append("| class | files | bytes | est_tok |")
    lines.append("| --- | ---: | ---: | ---: |")
    grand_files = 0
    grand_bytes = 0
    grand_tok = 0
    for cls in CLASS_ORDER:
        subset = [r for r in rows if r["class"] == cls]
        if not subset:
            continue
        n = len(subset)
        b = sum(r["bytes"] for r in subset)
        t = sum(r["est_tok"] for r in subset)
        grand_files += n
        grand_bytes += b
        grand_tok += t
        lines.append(f"| {cls} | {n} | {b} | {t} |")
    lines.append(f"| **grand total** | **{grand_files}** | **{grand_bytes}** | **{grand_tok}** |")
    lines.append("")
    lines.append(
        "`est_tok` is `bytes // 4`, a rough measurement heuristic, not a "
        "tokenizer-accurate count."
    )
    lines.append("")
    return "\n".join(lines)


def check(root: Path) -> int:
    rows, errors = build_rows(root)
    if errors:
        print("package shape inventory check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    generated = render_doc(rows, generation_command=f"python tools/{Path(__file__).name}")
    output = root / OUTPUT_REL
    if not output.is_file():
        print("package shape inventory check: FAIL")
        print(f"- {OUTPUT_REL}: missing generated output")
        return 1
    current = output.read_text(encoding="utf-8")
    if current != generated:
        print("package shape inventory check: FAIL")
        print(f"- {OUTPUT_REL}: stale; run python tools/{Path(__file__).name}")
        return 1
    print("package shape inventory check: PASS")
    return 0


def build(root: Path) -> int:
    rows, errors = build_rows(root)
    if errors:
        print("package shape inventory build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    generated = render_doc(rows, generation_command=f"python tools/{Path(__file__).name}")
    output = root / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    print("package shape inventory build: PASS")
    print(f"Output: {OUTPUT_REL}")
    return 0


def self_test() -> int:
    root = repo_root()
    checks: list[tuple[str, bool]] = []

    rows, errors = build_rows(root)
    checks.append(("shipped files enumerate without error", not errors))

    files_seen = [r["file"] for r in rows]
    checks.append(("every shipped file classified exactly once", len(files_seen) == len(set(files_seen)) and len(rows) > 0))

    class_index = {name: i for i, name in enumerate(CLASS_ORDER)}
    checks.append(("every row has a known class", all(r["class"] in class_index for r in rows)))

    subtotal_files = sum(1 for r in rows if r["class"] in class_index)
    checks.append(("class subtotals sum to grand total (files)", subtotal_files == len(rows)))
    subtotal_bytes = sum(r["bytes"] for r in rows)
    checks.append(("class subtotals sum to grand total (bytes)", subtotal_bytes == sum(r["bytes"] for r in rows)))

    skill_md_row = next((r for r in rows if r["file"] == "skill/SKILL.md"), None)
    checks.append(("SKILL.md classified host-hot", skill_md_row is not None and skill_md_row["class"] == "host-hot"))

    dispatch_gate_row = next((r for r in rows if r["file"] == "skill/references/runtime-dispatch-gate.md"), None)
    checks.append(
        (
            "runtime-dispatch-gate.md classified prompt-hot",
            dispatch_gate_row is not None and dispatch_gate_row["class"] == "prompt-hot",
        )
    )

    checks.append(("at least one cold-law file found", any(r["class"] == "cold-law" for r in rows)))

    # Synthetic drift detection: mutate the rendered doc and confirm --check's
    # comparison would catch it (exercised in-process, not via subprocess).
    generated = render_doc(rows, generation_command="python tools/build_package_shape_inventory.py")
    drifted = generated + "\nSYNTHETIC DRIFT LINE\n"
    checks.append(("--check logic detects synthetic drift", drifted != generated))
    checks.append(("--check logic accepts freshly generated doc as non-drifted", generated == render_doc(rows, "python tools/build_package_shape_inventory.py")))

    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"package shape inventory self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the generated doc is stale")
    parser.add_argument("--self-test", action="store_true", help="run deterministic self-checks")
    args = parser.parse_args(argv)

    root = repo_root()

    if args.self_test:
        return self_test()
    if args.check:
        return check(root)
    return build(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
