# Operating Discipline

## Purpose

This note keeps repo work practical: inspect the real artifact, align to the release/runtime
objective, prepare risky changes before forcing them, remove overload before adding process, and
fold small regressions into durable checks.

## Gemba

Go to the real place of work. For failures, inspect the actual file, generated HTML, package,
checker output, smoke artifact, workflow, or UI state. Do not diagnose from summaries when the live
artifact exists.

## Hoshin Kanri, light

For major workstreams, name:

- Objective: the top outcome.
- Owner/source of truth: the file, tool, schema, or docs owner.
- Metric/check: the command or evidence that tells whether it is aligned.
- Review: the next point before tag, release update, merge, or publication.

Example:

```text
Objective: v0.4.2.0 release-safe runtime package.
Owner/source: atomics/skill/** plus release docs.
Metric/check: package/provenance/smoke gates pass.
Review: before tag/release update.
```

Keep this lightweight; do not create heavy OKR bureaucracy for small fixes.

## Nemawashi

Lay groundwork before changing source ownership, checker policy, release gates, package behavior,
generated-doc architecture, or runtime entrypoint behavior. Surface the proposed change, affected
owners, tradeoffs, and rollback path before mutation.

Do not use Nemawashi to stall tiny safe fixes, typo repairs, or bounded checker-message cleanups.

## Muda / Mura / Muri

Cut waste, smooth uneven work, and reduce overload before adding more process or tools.

- Remove redundant panels, repeated headers, overloaded source maps, giant audit walls, and
  duplicated source-of-truth text.
- Prefer small source-owned renderers and checkers over broad frameworks.
- If a UI or docs surface is overloaded, reduce hierarchy and density before adding more panels.

## Kaizen

Improve the smallest repeatable part of the process, measure it, and fold it into the standard.
Every regression fix should ask what small checker, runbook, token, source-owner rule, or template
rule prevents recurrence.

## PDCA

Use PDCA for bounded improvement loops:

- Plan: name the smallest change, owner/source, risk, rollback, and verification.
- Do: patch only the agreed owner surface.
- Check: run the smallest meaningful smoke/check before claiming improvement.
- Act: standardize, revise, revert, defer, block, or mark unverified with a reason.

For `SKILL.md` cleanup, PDCA means taking a baseline smoke before mutation, changing only safe
pointer or entrypoint text, rebuilding generated runtime, running strict static checks, then taking
the post-change smoke with the same prompts and runtime-loaded capture method. If the reliable
local method is an inlined generated runtime, use it for both sides of the comparison and label it
local generated-runtime evidence, not package-bound release proof.

## Andon

Use Andon when work cannot honestly pass. Report:

- status;
- blocker;
- failing check or live artifact;
- owner/source of truth;
- next concrete action.

Examples:

- Release-smoke failure: stop tag/release work, name the failing smoke/checker, owner
  `tools/check_smoke_artifacts.py` plus release docs, and the next capture/check action.
- Package/provenance gate failure: stop upload, name the mismatched package/provenance field,
  owner `docs/release-artifacts.md` plus provenance JSON, and the smallest passing check.

## Hansei

Use Hansei after a failure or regression:

- Gap: what expectation failed?
- Cause: why did the current standard allow it?
- Countermeasure: what small owner/checker/runbook change addresses the cause?
- Follow-up evidence: what command, smoke, or inspection will prove the countermeasure?

For docs/index visual regression, the gap might be "Reference opens on provenance wall"; the cause
could be source-map order/default state; the countermeasure is generator/checker hierarchy repair;
the follow-up evidence is docs/index build/check plus browser inspection.

## 5 Whys

Use 5 Whys when the cause is not obvious. Stop when you reach a fixable process/source-owner cause,
not when blame lands on a person or model. Add the countermeasure at that cause.

Example for `SKILL.md` entrypoint cleanup:

```text
Symptom: Smoke B loses the noetic-field banner.
Why 1: The entrypoint pointer removed an always-loaded render invariant.
Why 2: The invariant existed in an owner file but was not loaded early enough.
Why 3: Cleanup treated DRY as deletion rather than progressive disclosure.
Countermeasure: restore the safety duplicate or add a stronger owner-load gate.
Follow-up evidence: rerun Smoke B and compiled-runtime freshness.
```

## Smoke Before Claim

Before readiness or improvement claims, run the smallest meaningful check and report the command
plus result. If live execution cannot run, label the evidence type and remaining risk. Static
checkers can prove freshness, shape, and contract conformance; they do not prove live model
behavior unless the check actually executes the model output path.

For local SKILL smoke diagnostics, first verify the generated runtime was actually loaded. If a
host cannot read `skill/SKILL.md` under its sandbox, inline the current generated runtime for local
diagnosis and label the result as generated-runtime evidence only. Do not treat that as
package-bound release-smoke proof.

## Plan Closure

End substantial work by mapping every planned item to:

- done;
- changed;
- blocked;
- deferred;
- unverified.

Do not leave planned items ambiguous. If a candidate was not patched because Smoke A made the risk
visible, mark it deferred and name the evidence.

## DRY / ACID / SSOT

- DRY: avoid duplicate source-of-truth logic. Preserve intentional safety duplicates in
  always-loaded runtime entrypoints when model behavior depends on seeing the invariant early.
- ACID: make changes atomic, consistent, isolated, and durable. Generated outputs should be
  rebuildable from owners; cleanup-only work should not change runtime semantics.
- SSOT: identify the source owner before editing. Patch the owner, not the nearest repeated
  sentence.

## Progressive disclosure

Always-loaded files should route, enforce gates, and name owner files. Detailed owner material
belongs in owner files. Generated docs should surface human-readable views first and move raw maps,
source provenance, and long matrices behind contextual disclosures unless the user is in an audit
view.

## Examples

Smoke failure triage:

- Gemba: inspect `output.md`, `trace.md`, `verdict.md`, `ir.json`, package SHA, and checker output.
- Hoshin: objective is release-safe evidence; owner is smoke checker plus release docs; metric is
  `python tools/check_smoke_artifacts.py --require-current-release-smokes`.
- Smoke Before Claim: run the strict smoke checker before readiness claims.
- Andon: stop if witness-required evidence fails; record the denied release action and smallest
  passing check.
- Hansei / 5 Whys: identify whether the gap is capture method, package provenance, witness-mode
  instructions, checker policy, or runtime output.
- Kaizen: add or strengthen the smallest checker that catches the failure class.

Docs/index visual regression:

- Inspect generated `docs/index.html` in a browser and the owner files under `docs/index/**`.
- Keep runtime meaning in `docs/index/runtime-architecture.json` and visual tokens in
  `docs/index/DESIGN.md`.
- Reduce overloaded provenance or duplicated panels before adding more UI.
- Run build/check plus browser inspection before claiming visual repair.

Generated docs source ownership:

- Do not hand-edit generated HTML.
- Patch source-owned sections, templates, runtime architecture JSON, generator, or checker.
- Rebuild and run docs/index checks.

Release gate failure:

- Deny tag, release asset upload, or release body update until package, provenance, and smoke gates
  pass.
- Report the denied action and smallest passing check.
- Close the plan by marking the release item blocked, deferred, or done only after the named check
  has evidence.

`SKILL.md` entrypoint cleanup:

- Keep entrypoint-critical runtime contract, routing gates, and safety duplicates visible.
- Convert detailed owner material into short pointers only after confirming the owner file already
  carries the rule and generated runtime freshness remains clean.
- Do not change runtime semantics during a cleanup-only pass.
- Run Smoke A before mutation and Smoke B afterward with the same prompts/capture method; if live
  execution is unavailable, say so and do not claim behavioral improvement.

## When not to over-process

Do not apply heavy alignment, consensus, or audit ceremony to tiny safe fixes. Do not invent a new
checker when a manual inspection is more honest and the automated signal would be noisy. Do not
move content out of an always-loaded entrypoint merely because it is duplicated if that duplicate is
a safety invariant for weak or compressed runtimes.
