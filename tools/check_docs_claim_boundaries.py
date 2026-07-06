#!/usr/bin/env python3
"""Docs claim-boundary checks (Plan 13).

Currently enforces ONE deterministic rule — R4 release-registry binding: every
published version documented in `docs/release-artifacts.md` (any version-shaped
`## vX.Y.Z.W ...` heading, regardless of suffix) at or above the v0.4.0.0 floor
must have a matching `## [vX.Y.Z.W]` heading in `CHANGELOG.md`. This closes the
gap that let v0.4.0.0 (a "Published Release Asset" heading, not "Release Package")
slip past `check_metacompliance_current_canon`'s narrower currency check, whose
RELEASE_ARTIFACT_RE only matches "Release Package" headings.

Rule R4 is structured version-heading parsing — deterministic, with no lexical
content scan, so it cannot overmatch prose.

DEFERRED (owner-scoped, not shipped here): lexical claim-verb rules (banned
unbounded phrases, Smoke-C compiled-output-mode disclosure, evidence-citation
requirements). A per-line lexical scan overmatches legitimate adjacent/defensive
prose — e.g. "Direct validators over the Smoke C outputs passed ..." is not a
Smoke-C-pass claim, and negated disclosures ("no guaranteed uptake") are not
violations. Those rules need a non-overmatching discriminator before they can be
gates. This checker deliberately does NOT re-own the `docs/non-claims.md`
sentence tokens already pinned by `check_metacompliance_current_canon`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ARTIFACTS = ROOT / "docs" / "release-artifacts.md"
CHANGELOG = ROOT / "CHANGELOG.md"
FLOOR = (0, 4, 0, 0)

RELEASE_HEADING_RE = re.compile(r"^## (v\d+\.\d+\.\d+\.\d+)\b", re.MULTILINE)
CHANGELOG_HEADING_RE = re.compile(r"^## \[(v\d+\.\d+\.\d+\.\d+)\]", re.MULTILINE)


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.removeprefix("v").split("."))


def release_versions_at_or_above_floor(release_text: str, floor: tuple[int, ...] = FLOOR) -> set[str]:
    return {v for v in RELEASE_HEADING_RE.findall(release_text) if version_key(v) >= floor}


def missing_release_versions(release_text: str, changelog_text: str, floor: tuple[int, ...] = FLOOR) -> list[str]:
    """Pure R4 core (unit-tested): released versions >= floor absent from CHANGELOG."""
    release = release_versions_at_or_above_floor(release_text, floor)
    changelog = set(CHANGELOG_HEADING_RE.findall(changelog_text))
    return sorted(release - changelog, key=version_key)


def self_test() -> int:
    rel = "## v0.4.0.0 Published Release Asset\n## v0.4.5.0 Release Package\n## v0.3.9.0 old\n"
    cl_missing = "## [v0.4.5.0] - x\n"                       # v0.4.0.0 absent
    cl_complete = "## [v0.4.0.0] - x\n## [v0.4.5.0] - x\n"
    checks = [
        ("missing version detected", missing_release_versions(rel, cl_missing) == ["v0.4.0.0"]),
        ("complete coverage accepted", missing_release_versions(rel, cl_complete) == []),
        ("below-floor version ignored", missing_release_versions("## v0.3.9.0 old\n", "") == []),
        ("suffix-agnostic (Published Release Asset counts)", "v0.4.0.0" in release_versions_at_or_above_floor(rel)),
    ]
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"docs claim-boundary self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    release_text = RELEASE_ARTIFACTS.read_text(encoding="utf-8")
    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    missing = missing_release_versions(release_text, changelog_text)
    if missing:
        print("docs claim-boundary check: FAIL")
        print(
            "- CHANGELOG.md is missing release-registry heading(s) for published version(s) "
            f"in docs/release-artifacts.md: {', '.join(missing)}"
        )
        return 1
    covered = len(release_versions_at_or_above_floor(release_text))
    print(f"docs claim-boundary check: PASS (R4 release-registry binding; {covered} versions >= v0.4.0.0 covered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
