# Release-Body Contract — Token Classification & De-Stale Decision

> Plan 06 deliverable, docs-only, **AWAITING OWNER SIGN-OFF** for the code change.
> Records which release-body tokens are invariant vs version-specific so a later
> owner-approved slice can generify or retire the v0.4.3.0-specific template WITHOUT
> changing active provenance verification. This document changes no runtime: the
> active `--provenance/--package` path and the stale-release-body guard are untouched.
> Dated 2026-07-04.

## Current state (shipped, unchanged)

`tools/check_release_provenance.py` carries a v0.4.3.0-specific release-body template
(`write_release_body`) and validator (`check_release_body`, required tokens at
lines 516-525). The stale-release-body guard (`stale_release_body_guard_error`,
`LEGACY_RELEASE_BODY_VERSION = "v0.4.3.0"`) already fails-safe for any non-legacy
version, so the template can never emit misleading text for a future release. The
CI/release workflow (`release-skill.yml`) uses only `--provenance/--package` and never
the release-body path; the v0.4.5.0 body was hand-written.

## Token classification

The `check_release_body` required-token set (lines 516-525), classified:

| Token | Class | Rationale |
| --- | --- | --- |
| `version` | INVARIANT | every release has a version |
| artifact name | INVARIANT | mechanical manifest field |
| artifact SHA256 | INVARIANT | mechanical manifest field |
| source commit | INVARIANT | mechanical manifest field |
| `Raw smoke outputs are local evidence` | INVARIANT | general evidence-boundary caveat every release must carry |
| `Repair14` | VERSION-SPECIFIC | a v0.4.3.0 episode proof-boundary claim |
| `route/curl` | VERSION-SPECIFIC | a v0.4.3.0 hotfix reference |
| `fresh hosted Smoke 7 model-output proof was not run` | VERSION-SPECIFIC | a v0.4.3.0 generated-burden caveat |

A generic (non-v0.4.3.0) release-body checker would retain the 5 invariant tokens and
drop the 3 version-specific ones. The MRP route-result vocabulary referenced inside
`write_release_body` is invariant runtime IR vocabulary owned by the diagnostic IR
schema, not a release-episode claim.

## Owner decisions (for a later post-sign-off code slice)

- **OD-06a — ratify the invariant/version-specific split** above. Prerequisite to any
  generify/retire change.
- **OD-06b — template disposition:** (i) DELETE `write_release_body`/`check_release_body`
  entirely (CI never uses them); (ii) reduce to a version-agnostic skeleton (invariant
  fields + caveats, per-release prose external); or (iii) keep legacy-only behind the
  existing guard. The live risk is already neutralized, so this is a de-stale/cleanup
  authorship decision, not a correctness fix.
- **OD-06c — manual preflight path:** keep the manual `--version/--artifact/--release-body`
  preflight sanctioned (and update the `AGENTS.md` v0.4.3.0 example) or retire it in
  favor of the workflow-only `--provenance/--package` path.

## What this does not do

- It changes no runtime, no checker, and no active `--provenance/--package` verification.
- It does not invent generic release-body semantics or tag/publish/release anything.
- Branch-protection / rulesets remain EXTERNAL-GATED.
