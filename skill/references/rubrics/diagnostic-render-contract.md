> role: governs visible render shape (Level 1 / 2 / 3); runs after output-release rubric, before public response; does not substitute for diagnosis or routing
> use when: deciding how visibly structured the response should be — ordinary prose, compact diagnostic, or full audit render
> do not use when: routing and owner selection are still in progress; render shape does not determine routing

# Diagnostic Render Contract

## Function

This file governs how visibly structured the output is. It runs after the output-release rubric has confirmed what may be released, and before the public response is shaped. It does not replace routing, does not determine what is diagnosed, and does not determine what is eligible for release. Render shape follows diagnosis; it does not govern it. Three levels are defined below. The default is Level 1 (ordinary bounded response). Levels 2 and 3 apply only when their specific conditions are met.

---

## Relation to Output-Release Rubric

The output-release rubric answers: *what may be released now, and in what order?*

This file answers: *how visibly structured should that release be?*

A response may pass the output-release rubric at Level 1 (compact answer needed) or at Level 2 (compact diagnostic warranted). The render contract selects the level and governs the visible shape within that level. It never determines what is eligible; it governs how eligible material appears.

---

## Render Levels

### Level 1 — Ordinary Bounded Response

**Use when:**
- The case has one clear governing burden.
- The user did not request diagnostic trace.
- No significant held/downstream distinction needs to be exposed.
- The corrective move is simple.
- P7 stop discipline favors brevity.

**Visible shape:** Ordinary prose. No diagnostic headers required. No template sections visible.

**Internal requirements still apply even when not visible:**
- Case-state resolved internally.
- Governing burden identified internally.
- Upstream blocker cleared or named.
- Downstream held if unresolved.
- Output-release rubric passed.
- Stop/hold/recurse decision made.
- State refresh considered before ending.

**Must not:**
- Pretend diagnosis was unnecessary.
- Release downstream content before upstream blockers clear.
- Hide held material when the user needs to know why the answer is bounded.
- Treat state refresh as only waiting for a user response.

---

### Level 2 — Compact Diagnostic / Lab-Report Response

**Use when:**
- The user invokes `/daee-epistemics`.
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

## Refresh / Stop / Hold / Recurse
- Refreshed state:
- Stop:
- Hold:
- Recurse only if:
```

**Rules:**
- Do not require every bullet if not materially governed.
- Do not expose PF codes or matched module names unless they help the user or audit trail.
- Do not let the diagnostic section become longer than the restorative answer unless the task is explicitly diagnostic/audit.
- Do not release downstream content merely because it is named in a section header.
- Do not treat compact diagnostic render as permission to dump all internal machinery.
- Do not treat the Refresh / Stop / Hold / Recurse section as merely waiting for user response. State whether same-response recursion is permitted and why.

---

### Level 3 — Full Diagnostic / Audit Render

**Use only when:**
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

## [Refresh / Stop / Hold / Recurse]
<Only include full detail when recursion, state-refresh, or pass-review materially governs the case.>

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
- `[Refresh / Stop / Hold / Recurse]` is conditional on whether recursion or state-refresh governs the case.
- Pass-Scoped Revision Notes are for audit/pass-review only — not ordinary runtime.

---

## Field Discipline

**When to surface PF codes / pattern_profile:** Only when the overlay changes routing, owner selection, hold/release behavior, or load floor — not as a label for the visible topic.

**When to surface matched module names / IDs:** Only in Level 3 full audit render, or in Level 2 when the user needs to trace which module governed a routing decision.

**When to surface backbone predicates:** Only when a backbone predicate emission (C, T, O, or K group) materially changed the routing gate or suppression rule in this pass.

**When to suppress all internal fields:** Level 1 ordinary response — always.

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

## Refresh / Stop / Hold / Recurse Section

This section appears in Level 2 and Level 3 when recursion, state-refresh, or the continuation decision materially governs the case.

It must answer:
- **Refreshed state:** What changed after the governing move? What remains live?
- **Stop:** Is there a stop condition active? Which one?
- **Hold:** What is held and why? Is the hold pass-scoped (traversal-delayed) or externally gated (requires user reply because a stop or register condition fires)?
- **Recurse only if:** What condition would license same-response recursion or a next bounded pass?

**Do not:**
- Treat this section as merely "I will continue in the next reply." State whether same-response recursion is permitted or blocked, and why.
- List this section when no recursion or stop/hold decision is live. Omit if Level 1 suffices.

---

## Prohibited Render Moves

1. **Render before diagnosis:** Do not populate template sections alongside answer-generation. Sections must be derived from a prior validated IR.
2. **Template-driven routing:** Do not let the presence of template fields determine what is diagnosed.
3. **Downstream-smuggling via section:** Do not release held content by naming it in a section header and then filling the section.
4. **Machinery dump as diagnostic transparency:** Diagnostic transparency means showing the governing fields — not every possible field.
5. **Level 3 as default:** Level 3 full audit render is not the default format. It applies only when the task is explicitly audit, regression, pass-review, or source-basis trace.
6. **Codex patch-report format as runtime output:** Patch-report structure (files inspected, implementation verdict, changelog) is not a runtime response format.
7. **Suppressing Level 2 when diagnostic transparency is needed:** If the user invoked `/daee-epistemics` or explicitly asked for diagnostic output, withholding Level 2 structure without a clear reason harms routing legibility.
8. **Hiding refreshed-state decision:** If a governing blocker was cleared in this pass and a downstream burden remains live, the response must show the refreshed-state decision — not silently hold the downstream material as though the blocker had not cleared.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/output-release.md` | Governs what may be released before this file governs how it appears |
| `references/diagnostics/framework-pipeline.md` | Canonical pipeline; ℛ (bounded render) sits here in the architecture |
| `references/diagnostics/case-state-schema.md` | `[Case State]`, `[Source Basis]`, `[Restoration Trace]` block schemas |
| `references/diagnostics/inference-boundary.md` | Source-basis marker legend (anchored / synthesis / inference / speculative) |
| `references/diagnostics/diagnostic-ir.md` | `output_shape`, `what_is_withheld_and_why`, `what_remains_live` — IR fields carrying release/render state |
| `references/procedures/P7-restoration-stops.md` | Stop discipline governs the Refresh / Stop / Hold / Recurse section |
| `skill/SKILL.md §V` | Surfaced-mode policy (ordinary vs. advanced mode); Two-Layer Output Contract |
| `references/diagnostics/anti-patterns.md` | `§Fixed Full-Field Template Materialization`, `§Template-Driven Routing` for prohibited failure modes |
