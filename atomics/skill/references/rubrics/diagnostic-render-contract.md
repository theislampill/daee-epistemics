---
id: diagnostic-render-contract
module_class: governance
canonical_path: skill/references/rubrics/diagnostic-render-contract.md
contract_version: "0.3.0.0"
load_when:
  - deciding how visibly structured the response should be (Level 1/2/3)
catalogue_registered: false
---

# Diagnostic Render Contract

## Function

This file governs how visibly structured the output is. It runs after the output-release rubric has confirmed what may be released, and before the public response is shaped. It also requires a post-render gate or compact final governance block before closure. It does not replace routing, does not determine what is diagnosed, and does not determine what is eligible for release. Render shape follows diagnosis; it does not govern it. Three levels are defined below. The default render mode is Level 1 (ordinary bounded response). Levels 2 and 3 apply only when their specific conditions are met.

## Canonical Render Mode Syntax

```text
/daee-epistemics
/daee-epistemics:dsl
/daee-epistemics:audit
```

- `/daee-epistemics` means default render mode: clean public-facing prose, readable sectioning, good final synthesis, internal recursive governance, and no giant load ledger by default.
- `/daee-epistemics:dsl` means compact DSL / lab-report mode: compressed Diagnostic IR or Case State, live door sequence, matched modules by original module IDs, held routes, State Refresh, and STOP / HOLD / RECURSE / PARTIAL.
- `/daee-epistemics:audit` means fuller procedural audit mode: may expose the runtime/bundle ledger, source-basis, diagnostic IR gate, routing gate, render permission, recursive passes, state refreshes, and final governance.

The old grim-reaper prompt is deprecated as a normal invocation pattern. Its useful discipline is internalized into the skill; use `:dsl` or `:audit` only when visible diagnostic structure is desired.

---

## Relation to Output-Release Rubric

The output-release rubric answers: *what may be released now, and in what order?*

This file answers: *how visibly structured should that release be?*

A response may pass the output-release rubric at Level 1 (compact answer needed) or at Level 2 (compact diagnostic warranted). The render contract selects the level and governs the visible shape within that level. It never determines what is eligible; it governs how eligible material appears.

---

## Render Levels

### Level 1 — Ordinary Bounded Response

**Use when:**
- The user invokes plain `/daee-epistemics`.
- The case has one clear governing burden.
- The user did not request diagnostic trace.
- No significant held/downstream distinction needs to be exposed.
- The corrective move is simple.
- P7 stop discipline favors brevity.

**Visible shape:** Ordinary prose. No diagnostic headers required. No template sections visible. Default mode is prose-first, but it still runs state refresh and recursive traversal internally.

**Internal requirements still apply even when not visible:**
- Case-state resolved internally.
- Governing burden identified internally.
- Upstream blocker cleared or named.
- Downstream held if unresolved.
- Output-release rubric passed.
- STOP / HOLD / RECURSE / PARTIAL decision made.
- Post-render gate run before ending.
- Compact final governance block rendered when the full gate is not surfaced.

**Must not:**
- Pretend diagnosis was unnecessary.
- Release downstream content before upstream blockers clear.
- Hide held material when the user needs to know why the answer is bounded.
- Treat state refresh as only waiting for a user response.
- Close with STOP before the post-render gate has rechecked held material.
- Stop after the first good move when the original input contains another eligible live door.
- Print a load ledger or full IR just because the skill was invoked.

---

### Level 2 — Compact Diagnostic / Lab-Report Response

**Use when:**
- The user invokes `/daee-epistemics:dsl`.
- The case has multiple live burdens.
- Diagnostic transparency materially helps.
- The answer must show what is governing first.
- Downstream material is held.
- Recursive traversal needs to be visible.
- The response needs to distinguish anchored, inferred, and speculative material.
- The user is testing whether the skill routed correctly.

**Recommended visible shape:**

```md
## Case State
- Governing burden:
- Active pressure:
- Upstream blocker:
- Downstream held:
- Route:
- Confidence:
- Decisive missing differentiator:

## Source Basis
- Anchored:
- Synthesis:
- Inference:
- Speculative / held:

## Release Check
- Cleared before release:
- Held downstream:
- Why this much is released:

## Restorative Response
<bounded answer>

## Post-Render Gate
- Cleared this pass:
- Remaining live distortions:
- Held routes rechecked:
- Newly released routes:
- Next eligible pass:
- Recursion decision: STOP | HOLD | RECURSE | PARTIAL
```

**Rules:**
- Do not require every bullet if not materially governed.
- Use original module IDs for any visible `matched_modules`; never use omnibus filenames as matched modules.
- Do not expose PF codes or matched module names unless they help the user or audit trail.
- Do not let the diagnostic section become longer than the restorative answer unless the task is explicitly diagnostic/audit.
- Do not release downstream content merely because it is named in a section header.
- Do not treat compact diagnostic render as permission to dump all internal machinery.
- Do not include the full verbose load ledger by default; that belongs to `:audit` only when useful.
- Do not treat the Post-Render Gate section as merely waiting for user response. State whether same-response recursion is required, blocked, partial, or complete and why.
- If recursive traversal is visible, use one door at a time: Live door, Why already present, Released module(s), Bounded move, State refresh, and Governance. Recursion is not argument dump.

---

### Level 3 — Full Diagnostic / Audit Render

**Use only when:**
- The user invokes `/daee-epistemics:audit`.
- The user asks for audit.
- The user asks for pass-review.
- The user asks for regression testing.
- The user asks for source-basis trace.
- The user asks whether the skill routed correctly.
- The task is a patch report or architecture test rather than answering an ordinary interlocutor.

**Full shape:**

```md
# Output — <Pass Number or "Initial daee-epistemics Response">

## Source Case
<input.md reference>

## [Case State]
- Case family:
- Claim-type:
- Claim level:
- Reason-category:
- Foreign-premise status:
- Upstream findings:
- Primary upstream issue:
- Pattern profile:
- Primary deformation:
- Routing gate:
- Read status:
- Live alternatives:
- Reassessment:
- Convergence requirement:
- Discourse orientation:
- Concealment mode:
- Register-hold:
- Deployable on shift to:
- Matched modules:
- Sequencing rationale:
- Restoration target:
- Confidence:
- Decisive missing differentiator:

## [Source Basis]
- [anchored]:
- [synthesis]:
- [inference]:
- [speculative]:
- Source type / weight:
- Restoration source:

## [Restoration Trace]
- Governing misread risk:
- What was withheld and why:
- What correction was applied:
- Route that became permissible after correction:
- What remains live or unresolved:

## [Restorative Response]
<Bounded public response. If Layer B is held, mark that clearly without releasing what remains held.>

## [Core Formulation]
<Only include when the objection, shubhah, or criterion structure needs explicit unpacking.>

## [Engagement Register]
<Only include when concealment mode, discourse orientation, register-hold, or Layer B / Layer A split materially governs deployment.>

## [Pastoral/Relational Note]
<Only include when non-intellectual conditions materially govern follow-through.>

## [Post-Render Gate]
<Required before closure; full detail is visible in Level 3.>

## Closing Formulation
<Sharp restorative closing.>

## Pass Tag
<pass-X or initial-daee-run>

## Pass-Scoped Revision Notes
<current-pass only; for audit/pass-review, not ordinary runtime.>
```

**Field discipline for Level 3:**
- `[Restorative Response]` is bounded, not exhaustive. If Layer B is held, it is held — not previewed under another heading.
- `[Core Formulation]` is conditional on whether the argument structure requires explicit unpacking.
- `[Engagement Register]` is conditional on whether concealment mode or orientation materially governs.
- `[Pastoral/Relational Note]` is conditional on whether non-intellectual conditions are operative.
- `[Post-Render Gate]` is mandatory in Level 3 and is derived from `post_render_gate`, not improvised after writing the answer.
- Pass-Scoped Revision Notes are for audit/pass-review only — not ordinary runtime.
- Runtime/bundle ledger, when shown, must resolve atomized paths through `compiled-module-map.json`; do not describe missing atomized files as literal runtime load targets.

---

## Field Discipline

**When to surface PF codes / pattern_profile:** Only when the overlay changes routing, owner selection, hold/release behavior, or load floor — not as a label for the visible topic.

**When to surface matched module names / IDs:** Only in Level 3 full audit render, or in Level 2 when the user needs to trace which module governed a routing decision.

**When to surface backbone predicates:** Only when a backbone predicate emission (C, T, O, or K group) materially changed the routing gate or suppression rule in this pass.

**When to suppress all internal fields:** Level 1 ordinary response suppresses diagnostic machinery, but it still runs the post-render gate internally and may surface a compact final governance sentence when the continuation decision materially affects the answer.

---

## Source Basis Discipline

Use the standard markers from `references/diagnostics/inference-boundary.md`:

| Marker | When |
|--------|------|
| `[anchored]` | Directly grounded in a loaded file or governing thesis |
| `[synthesis]` | Combining multiple loaded files without adding a new thesis |
| `[inference]` | Model-level extension beyond what the files explicitly state |
| `[speculative]` | Tentative extension that should not govern unless confirmed |

In Level 2, surface the Source Basis section only when the reply combines files, depends on synthesis, or uses model-level inference. In Level 1, inference marking is still required internally but need not appear in the visible output unless the claim is materially extension-dependent.

---

## Restoration Trace Discipline

`[Restoration Trace]` appears in Level 3 full audit render and may appear in Level 2 when the trace materially explains why only this much was released. It must record:

1. What governed the case.
2. What was withheld and why.
3. What correction was applied.
4. What route became permissible after correction.
5. What remains live or unresolved.

It does not appear in Level 1 and should not appear in Level 2 unless the held/released distinction is the primary diagnostic question.

---

## Layer B and Held Material

**Layer B held means actually held.** Not previewed. Not named as held and then summarized. Not answered under a different heading (see `anti-patterns.md §Held-but-Answered Contradiction`).

In a Level 2 compact render, held material may be named in the `Downstream held` field of the Case State section and in the `Held downstream` field of the Release Check section. These fields name what is held; they do not summarize or preview the held content.

In a Level 3 full render, the `[Restorative Response]` must mark held Layer B deployment explicitly: "Layer B: held — [reason]." The content does not appear.

---

## Post-Render Gate / Final Governance Section

This section is mandatory in the governing state after every bounded restorative move. Level 2 and
Level 3 surface the full gate when recursion, state-refresh, or the continuation decision materially
governs the visible answer. Level 1 may compress it into a final governance block, but the block
must still name the recursion decision and next eligible pass.

It must answer:
- **Cleared this pass:** What did the bounded move actually clear?
- **Remaining live distortions:** What pressure remains live in the same input?
- **Held routes rechecked:** Which held routes were tested after refresh?
- **Newly released routes:** Did any held route become newly eligible?
- **Next eligible pass:** What is the next bounded pass, or is there none?
- **Recursion decision:** STOP, HOLD, RECURSE, or PARTIAL.

Decision rules:
- **STOP** is valid only if no live distortion remains, no eligible live door remains, and no held route has become eligible.
- **HOLD** is valid only if remaining material exists but its release signal is absent from the input.
- **RECURSE** is required if another live distortion remains in the same input or a held route becomes eligible.
- **PARTIAL** is required if token, tool, or interaction limits prevent completion while recursive pressure remains.

**Do not:**
- Treat this section as merely "I will continue in the next reply." State whether same-response recursion is permitted or blocked, and why.
- Emit STOP without this section or its compact final-governance equivalent.
- Use PARTIAL as an excuse to dump a queue. It names the next eligible pass that limits prevented.

---

## Prohibited Render Moves

1. **Render before diagnosis:** Do not populate template sections alongside answer-generation. Sections must be derived from a prior validated IR.
2. **Template-driven routing:** Do not let the presence of template fields determine what is diagnosed.
3. **Downstream-smuggling via section:** Do not release held content by naming it in a section header and then filling the section.
4. **Machinery dump as diagnostic transparency:** Diagnostic transparency means showing the governing fields — not every possible field.
5. **Level 3 as default:** Level 3 full audit render is not the default format. It applies only when the task is explicitly audit, regression, pass-review, or source-basis trace.
6. **Codex patch-report format as runtime output:** Patch-report structure (files inspected, implementation verdict, changelog) is not a runtime response format.
7. **Suppressing Level 2 when diagnostic transparency is needed:** If the user invoked `/daee-epistemics:dsl` or explicitly asked for compact diagnostic output, withholding Level 2 structure without a clear reason harms routing legibility.
8. **Hiding refreshed-state decision:** If a governing blocker was cleared in this pass and a downstream burden remains live, the response must show the refreshed-state decision — not silently hold the downstream material as though the blocker had not cleared.
9. **Premature closure without re-entry:** Do not render one strong move and close without running the post-render gate, rechecking held routes, and naming STOP, HOLD, RECURSE, or PARTIAL.
10. **Printing the IR schema as the response:** Do not print the `[Diagnostic IR]` code-fenced block or a `## Diagnostic IR` section header in the public response in default mode. The Full IR Schema in `diagnostic-ir.md` is the internal state object for the dispatch gate — not a printout template. Discipline is universal; printout is mode-specific. The grim-reaper discipline applies in every mode; the grim-reaper printout belongs to `:audit`. In default mode, a compact final-governance sentence naming the recursion decision is permitted; the full IR block is not.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/output-release.md` | Governs what may be released before this file governs how it appears |
| `references/diagnostics/framework-pipeline.md` | Canonical pipeline; ℛ (bounded render) sits here in the architecture |
| `references/diagnostics/case-state-schema.md` | `[Case State]`, `[Source Basis]`, `[Restoration Trace]` block schemas |
| `references/diagnostic