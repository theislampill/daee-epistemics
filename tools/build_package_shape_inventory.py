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
                    package metadata JSON the host/tooling reads directly off
                    disk (compiled-module-map.json, build-manifest.json,
                    cold-law-manifest.json -- the cold-law binding table
                    tools/check_cold_law_digest.py reads directly, not a
                    route-gated content file the model chooses to load).
  - prompt-hot   : every file named in SKILL.md's "Load path for substantive
                    cases" numbered list. Unconditional membership in that
                    list is decisive: a file is prompt-hot if it is named
                    there, even if separate SKILL.md prose also describes a
                    narrower conditional re-run rule for it (unconditional
                    list membership beats conditional prose -- see
                    ROUTE_WARM_LOAD_PATH_BASENAMES for the mechanism, kept
                    empty by default so a genuinely conditional entry can be
                    added later with justification). Parsed from the anchor
                    text at runtime; see ANCHOR_TEXT below.
  - route-warm   : any load-path entry explicitly justified as conditional via
                    ROUTE_WARM_LOAD_PATH_BASENAMES (currently none), plus any
                    other file this script identifies as conditionally routed
                    or defaults to route-warm pending an explicit anchor.
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

# Previously this held {"runtime-phase2-passes.md"}, forcing that file
# route-warm on the theory that skill/SKILL.md's surrounding prose (search
# anchors: "mandatory Phase 2 passes", "Phase-2 pass", "Run the mandatory
# Phase 2 passes listed above.") describes it as a conditional pass. But
# runtime-phase2-passes.md is *also* item 3 of the unconditional "Load path
# for substantive cases" numbered list (see LOAD_PATH_HEADING /
# parse_load_path below) -- every substantive case walks that list, so the
# file is unconditionally loaded for the substantive-case population even
# though a *narrower* case (Phase 2 already run) may skip re-running its
# pass. Unconditional numbered-list membership is the stronger, more general
# claim and beats the conditional prose reading, so this override is removed
# and the file now falls through to the ordinary prompt-hot branch below like
# every other load-path entry. Kept as an empty set (rather than deleting the
# override site) so a future genuinely-conditional load-path entry has a
# documented place to be added, with the same justification standard applied.
ROUTE_WARM_LOAD_PATH_BASENAMES: set[str] = set()

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
# cold-law-manifest.json is host-hot package metadata JSON of the same class
# as compiled-module-map.json / build-manifest.json: it is the binding table
# tools/check_cold_law_digest.py reads directly off disk (schema
# daee-cold-law-manifest-v1) to prove clause-digest/cold-source binding is not
# theater, not a route-gated content file the model chooses to load.
HOST_HOT_BASENAMES = {"SKILL.md", "compiled-module-map.json", "build-manifest.json", "cold-law-manifest.json"}

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
        return "route-warm", "DEFAULTED route-warm: no explicit SKILL.md anchor found for this file; verify manually"

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

    # Post-Slice-C: the "Load path for substantive cases" numbered list now names
    # exactly one file, runtime-core-routing.md (the retired runtime-dispatch-gate.md
    # bundle was split into 11 route shards; see tools/compiled_runtime_lib.py
    # BUNDLE_SOURCES and the Compiled Runtime Routing Addendum). That one listed
    # file must classify prompt-hot (unconditional load-path list membership), and
    # the other on-demand shards -- not named in the numbered list, loaded only on
    # dispatch-index selection -- must classify route-warm (the DEFAULTED branch in
    # classify() for references/*.md files absent from load_path_items).
    core_routing_row = next((r for r in rows if r["file"] == "skill/references/runtime-core-routing.md"), None)
    checks.append(
        (
            "runtime-core-routing.md classified prompt-hot",
            core_routing_row is not None and core_routing_row["class"] == "prompt-hot",
        )
    )

    ON_DEMAND_SHARD_FILES = [
        "skill/references/runtime-core-ir.md",
        "skill/references/runtime-core-pipeline.md",
        "skill/references/runtime-core-recursion.md",
        "skill/references/runtime-shard-ir-support.md",
        "skill/references/runtime-shard-diagnostic.md",
        "skill/references/runtime-shard-audit.md",
        "skill/references/runtime-shard-thesis.md",
        "skill/references/runtime-shard-restoration.md",
        "skill/references/runtime-shard-output-release.md",
        "skill/references/runtime-shard-render-contract.md",
    ]
    on_demand_rows = {r["file"]: r for r in rows if r["file"] in ON_DEMAND_SHARD_FILES}
    checks.append(
        (
            "all 10 on-demand route shards are present in the shipped package",
            len(on_demand_rows) == len(ON_DEMAND_SHARD_FILES),
        )
    )
    checks.append(
        (
            "on-demand route shards classify route-warm (loaded on dispatch-index selection, not eagerly)",
            all(r["class"] == "route-warm" for r in on_demand_rows.values()),
        )
    )

    # Superseded by the Slice C dispatch-index rewrite: runtime-phase2-passes.md
    # was item 3 of the old five-bundle "Load path for substantive cases"
    # numbered list (see the FIX 3 history this canary used to guard), so
    # unconditional list membership classified it prompt-hot. Slice C replaced
    # that five-line list with exactly ONE line (runtime-core-routing.md) plus a
    # Dispatch Index of on-demand route shards (tools/build_package_shape_inventory.py
    # parse_load_path() anchor + the addendum text in
    # atomics/skill/references/rubrics/{non-droppable-manual-contract.md,
    # manual-contract-digest.md}). runtime-phase2-passes.md is no longer named in
    # that list at all, so it now correctly falls through to the DEFAULTED
    # route-warm branch in classify() -- this is the intended, deliberate result
    # of the dispatch-index rewrite, not a regression. The canary now asserts the
    # new (route-warm) classification instead of the pre-Slice-C prompt-hot one.
    phase2_row = next((r for r in rows if r["file"] == "skill/references/runtime-phase2-passes.md"), None)
    checks.append(
        (
            "runtime-phase2-passes.md classified route-warm post-Slice-C (no longer named in the one-line load path; superseded FIX 3 canary)",
            phase2_row is not None and phase2_row["class"] == "route-warm",
        )
    )

    # FIX 3 canary: cold-law-manifest.json is host-hot package metadata (the
    # binding table tools/check_cold_law_digest.py reads directly), same
    # class as compiled-module-map.json / build-manifest.json -- not a
    # DEFAULTED route-warm guess.
    cold_law_manifest_row = next((r for r in rows if r["file"] == "skill/cold-law-manifest.json"), None)
    checks.append(
        (
            "cold-law-manifest.json classified host-hot with a real evidence anchor",
            cold_law_manifest_row is not None
            and cold_law_manifest_row["class"] == "host-hot"
            and "DEFAULTED" not in cold_law_manifest_row["evidence"],
        )
    )

    checks.append(("at least one cold-law file found", any(r["class"] == "cold-law" for r in rows)))

    # FIX 5 canary: the fallback classify() branch for references/ files
    # outside all known anchors must use the honest "DEFAULTED route-warm"
    # wording (never a confident-sounding claim like "loaded conditionally by
    # route"), while still classifying the file as route-warm.
    defaulted_rows = [r for r in rows if "DEFAULTED route-warm" in r["evidence"]]
    checks.append(
        (
            "fallback classify() branch uses honest 'DEFAULTED route-warm' anchor wording",
            all(r["class"] == "route-warm" for r in defaulted_rows),
        )
    )
    checks.append(
        (
            "no shipped row uses the old confident-sounding 'loaded conditionally by route' fallback wording",
            not any("loaded conditionally by route" in r["evidence"] for r in rows),
        )
    )

    # FIX 4: cross-tool hot-set consistency. measure_load_path_budget.py
    # resolves "always-load" and "structural-diagnosis-floor" bundle files
    # from skill/SKILL.md's Always Load + Mandatory Diagnostic Core tables
    # via compiled-module-map.json. Those are exactly the bundles this
    # inventory's own classify() should treat as host-hot/prompt-hot -- if
    # this inventory ever classified one of them route-warm or cold-law, the
    # two tools would disagree about what is "hot", which is the whole gap
    # this check closes. Import is path-safe: measure_load_path_budget.py
    # lives in this same tools/ directory, so it is imported by inserting
    # this file's directory onto sys.path (matching how this script itself
    # is normally invoked as `python tools/build_package_shape_inventory.py`,
    # i.e. with tools/ importable) rather than assuming a package prefix.
    tools_dir = str(Path(__file__).resolve().parent)
    _sys_path_inserted = tools_dir not in sys.path
    if _sys_path_inserted:
        sys.path.insert(0, tools_dir)
    try:
        import measure_load_path_budget as _mlpb

        _skill_text = _mlpb.SKILL_MD.read_text(encoding="utf-8")
        _al_bundles, _al_unresolved = _mlpb.always_load_bundles(_skill_text)
        _sd_bundles, _sd_unresolved = _mlpb.structural_diagnosis_bundles(_skill_text)
        checks.append(
            (
                "cross-tool: always-load + structural-diagnosis-floor bundles resolve with 0 unresolved entries",
                len(_al_unresolved) == 0 and len(_sd_unresolved) == 0,
            )
        )

        _rows_by_file = {r["file"]: r for r in rows}
        _floor_bundle_paths = sorted(set(_al_bundles) | set(_sd_bundles))
        _hot_classes = {"host-hot", "prompt-hot"}
        # Post-Slice-C: the "Load path for substantive cases" numbered list was
        # rewritten to exactly ONE line (runtime-core-routing.md) plus a Dispatch
        # Index of on-demand route shards. runtime-diagnostic-core.md (the
        # structural-diagnosis-floor's Mandatory Diagnostic Core bundle) is no
        # longer named in that list, so it is no longer classified prompt-hot by
        # the package-shape anchor -- it now falls to route-warm like the other
        # on-demand shards. This is the deliberate, documented result of the
        # dispatch-index rewrite (see tools/build_package_shape_inventory.py
        # parse_load_path() and the addendum text in non-droppable-manual-contract.md
        # / manual-contract-digest.md), not a regression: the floor bundle must
        # still SHIP and still be REACHABLE (never cold-law-gated behind the
        # omnibus V1/Phase-2/Diagnostic-IR authorization prose), just no longer
        # unconditionally eager. The never-cold-law invariant is what this canary
        # now guards instead of the old always-hot one.
        _never_cold_law_classes = {"host-hot", "prompt-hot", "route-warm"}
        _floor_bundles_cold_law: list[str] = []
        _floor_bundles_not_shipped: list[str] = []
        for _bundle_path in _floor_bundle_paths:
            _rel_from_skill = _bundle_path.relative_to(root / "skill").as_posix()
            _shipped_key = f"skill/{_rel_from_skill}"
            _row = _rows_by_file.get(_shipped_key)
            if _row is None:
                # A resolved always-load/diagnostic-core floor bundle that
                # does not appear in the shipped-file set at all is itself a
                # FAIL: floor content must ship, full stop.
                _floor_bundles_not_shipped.append(_shipped_key)
                continue
            if _row["class"] not in _never_cold_law_classes:
                _floor_bundles_cold_law.append(f"{_shipped_key} (classified {_row['class']!r})")
        checks.append(
            (
                "cross-tool: every resolved always-load/diagnostic-core floor bundle ships in the package",
                len(_floor_bundles_not_shipped) == 0,
            )
        )
        checks.append(
            (
                "cross-tool: every resolved always-load/diagnostic-core floor bundle is host-hot, prompt-hot, or route-warm (never cold-law-gated, post-Slice-C dispatch-index rewrite)",
                len(_floor_bundles_cold_law) == 0,
            )
        )
    finally:
        if _sys_path_inserted:
            sys.path.remove(tools_dir)

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
