<!--
GENERATED FILE.
Do not edit directly.
Canonical atomized source lives under atomics/skill/.
Regenerate with tools/build_compiled_runtime.py.
-->

# runtime-output-governance

This generated bundle is a runtime read view. Section presence does not imply active dispatch.


## SOURCE MODULE: output-release

<!-- SOURCE: atomics/skill/references/rubrics/output-release.md -->
<!-- MODULE_ID: output-release -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: atomics/skill/references/rubrics/output-release.md -->
<!-- SOURCE_SHA256: 9f6ce4799207e4118196665700b53a9565711ec3c192c1ca7b75e641b4a5bb16 -->

---
id: output-release
module_class: governance
canonical_path: skill/references/rubrics/output-release.md
contract_version: "0.3.0.0"
load_when:
  - any response about to be shaped or released
routing_effects:
  - governs how much may be released, in what order, and under what case-state conditions
catalogue_registered: false
---

# Output-Release Rubric

## Function

This is a runtime governance rubric. It runs after the dispatch gate has opened and routing has identified the governing burden, active claim-level / PF overlay, canonical owners, matched modules, and family-local load floor. It runs before final public render, and it forces a post-render re-entry gate before closure. It governs: (1) how much content may be released; (2) in what order; (3) under what case-state constraints; (4) when downstream content must remain held; (5) when held content must be reassessed after refresh; (6) when compact diagnostic render is appropriate; (7) when recursive traversal is required inside the same response; and (8) why STOP, HOLD, RECURSE, or PARTIAL is the correct closure state. It is not a topic bank, not an argument bank, not a mandate to expose all internal diagnostic fields, and it does not require every answer to visibly print every template section.

## Pipeline Position

```
raw discourse
→ noetic / memetic pressure read
→ typed IR
→ PF atom(s) / claim-level overlay
→ canonical owner(s)
→ matched TTP route
→ family-local load floor
→ output-release rubric        ← THIS FILE
→ diagnostic render contract
→ bounded public response
→ post-render state refresh / re-entry gate
→ STOP / HOLD / RECURSE / PARTIAL
→ next governed pass if eligible
```

**Division of labour:**
- Routing decides what is eligible.
- Canonical owners decide what must be addressed.
- Family-local load floor decides what must be loaded.
- Output-release rubric decides what may be released now.
- Diagnostic render contract decides how visibly structured the output is.
- Post-render gate reassesses what remains live, drops, compresses, or becomes eligible.
- P7 stop discipline constrains the gate's STOP, HOLD, RECURSE, or PARTIAL decision.

Do not collapse these into one step. Do not let visible render shape determine routing.

---

## What This Rubric Is Not

```
Rubric ≠ template.
Render contract ≠ routing engine.
Diagnostic transparency ≠ machinery dump.
Compact lab report ≠ exhaustive audit report.
Default mode ≠ giant load ledger.
Plain /daee-epistemics ≠ DSL lab report.
Held downstream ≠ answered downstream.
Held downstream ≠ never answer.
Held downstream ≠ wait for user reply only.
State refresh ≠ external response only.
Recursive traversal ≠ argument dump.
Source basis ≠ proof bank.
Layer B release ≠ total framework materialization.
P7 stop ≠ failure to answer.
STOP ≠ valid before post-render gate.
Abstraction ≠ restoration.
Patch report ≠ runtime output.
```

**Core principle:**

> Held means not released at the current traversal point. Apply the governing TTP, refresh state, then reassess upstream, downstream, first-order, and higher-order burdens. If another burden remains live and permitted, continue with the next bounded pass; stop only when P7, register, semantic, thin-basis, or sufficiency governance requires stopping.

> Held means traversal-delayed, not response-delayed.

> State refresh is not identical to waiting for a new user response. A fresh differentiating signal may arise inside the same response when the prior governing blocker has been cleared by the response itself and the next live burden is now visible. However, same-response recursion must remain bounded by P7, release discipline, and the smallest sufficient restorative move.

> STOP is invalid unless the post-render gate has run. If the gate finds another live distortion in the same input or a held route newly eligible, RECURSE is required. If the route remains live but blocked, HOLD is required. If limits prevent the next eligible pass, PARTIAL is required.

> No premature STOP: if an eligible live door already present in the original input remains after the current blocker clears, the response must RECURSE into one bounded next pass or mark PARTIAL if limits prevent it. HOLD is valid only when the release signal is absent. Recursion is not argument dump; it is one door at a time under refreshed governance.

> Render mode does not change governance. Default `/daee-epistemics` mode keeps the answer clean and prose-first while running recursive traversal internally. `/daee-epistemics:dsl` exposes compact Diagnostic IR / live-door state. `/daee-epistemics:audit` may expose the fuller procedural and runtime/bundle ledger. The old grim-reaper prompt is deprecated as normal prompting because its useful discipline is now native.

---

## Release Question

Before releasing any content, ask: *Is this response releasing the right content, in the right order, for the current refreshed case-state — no more, no less, not before upstream blockers clear?*

---

## Post-Render Re-Entry Gate

After every bounded restorative move, before closing the response, run the State Refresh /
Re-Entry Gate and populate the IR `post_render_gate`:

```text
post_render_gate:
  cleared_this_pass:
  remaining_live_distortions:
  held_routes_rechecked:
  newly_released_routes:
  next_eligible_pass:
  recursion_decision: STOP | HOLD | RECURSE | PARTIAL
```

The gate must answer:

1. What was cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. Is there a next eligible pass?
6. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

Decision rules:

- `STOP`: valid only if no live distortion remains, no eligible live door remains, and no held route has become eligible.
- `HOLD`: valid only if remaining material exists but its release signal is absent from the input.
- `RECURSE`: required if another live distortion remains in the same input or a held route becomes eligible.
- `PARTIAL`: required if token, tool, or interaction limits prevent completion while recursive pressure remains.

STOP cannot be emitted before this gate runs. Held material must be rechecked after each pass.

---

## Pass/Fail Checks

### 1. Governing Burden Identified

**Pass:**
- The response identifies the live governing blocker or pressure family.
- The response does not answer a downstream doctrinal question before the upstream blocker clears.
- The visible topic is not mistaken for the governing issue.

**Fail:**
- The response treats the visible topic as the governing issue while ignoring a stronger upstream blocker.
- The response answers first-order content while semantic, lexical, authority-order, proof-method, tribunal, register, or stop pressure remains unresolved.

**Upstream blockers that must clear before downstream release:**

| Blocker | Owning file |
|---------|-------------|
| Lexical-ontological trap / loaded term | `tactics/M9-predication-mode.md` |
| Semantic neutralization (recontenting / evacuation) | `diagnostics/prophetic-discourse-neutralization.md` |
| Authority-order inversion | `diagnostics/foreign-premise-detection.md` §O-1 |
| Imported criterion or tribunal | `diagnostics/foreign-premise-detection.md` |
| Static-perfection tribunal | `diagnostics/perfection-criterion-usurpation.md` |
| Proof-method overreach | `diagnostics/proof-method-audit.md` |
| Definition / conception capture | `diagnostics/definition-discipline.md` |
| Causal-series confusion / regress | `diagnostics/causal-series-taxonomy.md` |
| Necessity/contingency proof-grammar overreach | `diagnostics/proof-method-audit.md` |
| Composition / dependence pressure | `case-library/do-attribute-precision.md` via `tactics/M9-predication-mode.md` |
| Occurrence-to-createdness collapse | `diagnostics/kalamic-interlocutor.md` |
| Over-intellectualization / abstraction-as-cure pressure | `anti-patterns.md §Transcendence Default / Abstraction-as-Cure` |
| Grief / register hold | `procedures/P7-restoration-stops.md` Stop 1 |
| Thin-basis underdetermination | `procedures/P7-restoration-stops.md` Stop 4 |

---

### 2. No Excess Release

**Pass:**
- The response releases only the smallest sufficient corrective move for the current refreshed state.
- It does not expose more framework machinery than the case requires.
- It does not stack arguments after the governing move has landed.
- It does not convert restoration into a concession press.
- It does not expand merely because more owners or proof-lines are available.

**Fail:**
- The response dumps multiple owners, arguments, diagnostics, or proof-lines when the case only required one governing move.
- The response continues after recognition or contact has surfaced.
- The response escalates into theoretical density when a bounded corrective move would suffice.

---

### 3. All Live Upstream Requirements Satisfied Before Downstream Release

Downstream content must remain held while any of the following are active:

- Loaded term / lexical trap → disambiguate before answering yes/no
- Imported perfection or static-deity tribunal → refuse tribunal-status before attribute content
- Semantic neutralization of revelation → handle that blocker before first-order interpretation
- Authority-order inversion → route through O-1 before ordinary reason/revelation tension
- Proof-method pressure → audit the proof architecture before deploying the proof
- Definition capture → clear public-language vs. technical capture before the contradiction claim
- Causal/regress pressure → classify the series before cosmological-argument prose
- Occurrence-to-createdness collapse → separate occurrence, divine act, product, and modality first
- Composition/dependence pressure → clear lexical/category/definition discipline first
- Necessity/contingency proof grammar → audit what the proof can and cannot establish
- Over-intellectualization → check whether live need is restoration, recognition, testimony, practice, or order of the knower; do not answer with more abstraction
- Grief/register hold → do not deploy intellectual content as though it were a seminar question

**Fail condition:** Any of these blockers active when doctrinal content is released.

---

### 4. Held Material Is Actually Held, Then Reassessed

**Pass:**
- Downstream material may be named as downstream but not fully released before its governing conditions are met.
- Holding is pass-scoped and traversal-scoped, not permanent suppression.
- The response distinguishes what is cleared, what is held, and what is not yet permitted.
- After the current governing move, the case-state is refreshed.
- If held material remains live and now governs, it becomes eligible for the next bounded pass.
- If held material no longer governs, it is dropped, compressed, or marked resolved.

**Permitted formulation:**

> X governs first; Y is live but held; Z is downstream and not yet released.
> After X is addressed, refresh state. If Y still governs, Y becomes the next bounded pass.

**Recursive rule:**

After X is addressed, refresh the case-state. If Y remains live, it becomes eligible for the next governed pass with its matched owner and TTP route. If Y no longer governs, it is dropped or compressed. The skill may move recursively through a single noetic structure's concealments and distortions, but each movement must be ordered, justified, and bounded.

**Fail:**
- The response says a downstream issue is held, then effectively answers it in the same pass anyway.
- The response treats held as never answer.
- The response treats held as only waiting for a new user reply.
- The response recurses into downstream issues without refreshing case-state.
- The response treats recursion as permission to dump every downstream argument at a single state refresh.
- The response bypasses Layer A / Layer B discipline by answering all doors at once.

---

### 5. Recursive Traversal Discipline

**Pass:** The response may proceed through multiple burdens only by governed traversal in this order:

1. Identify current governing blocker.
2. Apply matched owner/TTP.
3. Explain restoration movement.
4. Refresh case-state.
5. Re-run matched TTP logic over remaining upstream, downstream, first-order, and higher-order burdens.
6. Release next item only if it remains live and now governs.
7. Run the post-render gate before closure.
8. STOP only when P7 / register / semantic / sufficiency governance permits it and no next eligible pass remains.

Recursive pass shape for Level 2/3 audit render:

```text
Live door:
Why already present:
Released module(s):
Bounded move:
State refresh:
Governance: STOP / HOLD / RECURSE / PARTIAL
```

Ordinary Level 1 answers may compress this shape, but the state refresh and decision still govern.

**Fail:**
- The response collapses recursive traversal into a single argumentative dump.
- The response treats every detected issue as immediately releasable.
- The response fails to explain how the movement restores order.
- The response keeps visiting downstream doors after restoration or contact has already landed.
- The response holds downstream material but never reassesses it after a governing blocker clears.
- The response stops after one strong move without running the post-render gate.

---

### 6. Bounded Layer B

**Pass:**
- The public answer gives the smallest sufficient Layer B corrective move for the current pass.
- It avoids unnecessary diagnostic labels, owner names, PF codes, or theoretical explanation unless the case or user request calls for diagnostic visibility.
- It remains case-sensitive rather than globally templated.
- It may use compact lab-report form, but only with fields that materially serve the case.

**Fail:**
- The response turns internal machinery into the public answer without need.
- The response prints a full diagnostic structure by default even when only a compact answer is needed.
- The response confuses patch-report format with runtime skill output.
- The response treats diagnostic transparency as permission for exhaustive machinery exposure.

---

### 7. Post-Render STOP / HOLD / RECURSE / PARTIAL Decision

**Pass:**
- The response runs the post-render gate before any closure decision.
- It records what cleared, what remains live, which held routes were rechecked, and whether any route became newly eligible.
- If recognition or contact has surfaced and no next live distortion remains, STOP may be recorded.
- If the case needs another pass but release is blocked, mark it as HOLD rather than dumping everything.
- If the current pass itself clears an upstream blocker and another burden remains live, same-response recursion is required as a bounded next pass unless a stop, register-hold, semantic gate, thin-basis rule, or limit blocks it.
- If limits prevent the next eligible pass, mark PARTIAL and name the next eligible pass.
- The response preserves P7 stop discipline.
- The response does not continue merely because additional related issues are available.

**Fail:**
- The response keeps expanding after the governing move has landed.
- The response answers every related issue because it is available, rather than because the refreshed case-state requires it.
- The response turns a restorative contact into a verbal concession press.
- The response treats stop discipline as permanent refusal when a refreshed state would permit a later bounded pass.
- The response emits STOP while `remaining_live_distortions` or `newly_released_routes` is non-empty.
- The response emits STOP because of token/tool limits while recursive pressure remains; this must be PARTIAL.

---

### 8. Diagnostic Render Eligibility

**Pass — compact diagnostic render is allowed or preferred when:**
- The user invokes `/daee-epistemics:dsl`.
- The user asks for diagnostic transparency.
- The case involves multiple live burdens.
- The case requires held/downstream distinction.
- Recursive traversal needs to be visible.
- An audit, regression, or pass-review is being performed.
- The response needs to show why a downstream answer is not yet released.
- The user is testing whether the skill routed correctly.

**Fail:**
- The response uses a full lab-report layout when the case only requires a short bounded corrective answer.
- The response hides necessary routing information when the user explicitly asked for diagnostic skill execution.
- Plain `/daee-epistemics` is treated as a giant ledger or full IR dump by default.
- The response exposes all possible fields rather than the materially governing fields.

---

### 9. Not a Mandatory Full-Field Template

This rubric governs output release. It does not impose a mandatory full-field public format. Runtime output remains governed by validated IR, bounded Layer B, diagnostic render eligibility, recursive state refresh, and STOP / HOLD / RECURSE / PARTIAL discipline.

Do not convert patch-report requirements into the skill's normal runtime response format.

Compact diagnostic structure is permitted when it serves the case. Exhaustive field materialization is not permitted unless the task is audit, regression, pass-review, or explicitly diagnostic.

---

## Failure Tests

### FT-1 — Loaded term
**Input:** Is God a body?
**Bad output:** Yes/no answer before disambiguating body/jism.
**Required behavior:** Split the loaded term (ordinary and technical senses) before doctrinal answer; block false sense-shift; hold downstream attribute content until cleared.

### FT-2 — Static perfection tribunal
**Input:** A God who speaks or acts in time cannot be perfect.
**Bad output:** Generic attribute answer or anthropomorphism answer before handling imported perfection tribunal.
**Required behavior:** Identify imported/static perfection tribunal; refuse tribunal-status; then route downstream to speech/action, predication, composition, or attribute content as appropriate.

### FT-3 — Semantic neutralization
**Input:** We affirm the text, but it gives no determinate guidance here.
**Bad output:** First-order interpretation before handling semantic neutralization.
**Required behavior:** Distinguish ordinary interpretation from guidance-nullification; handle semantic neutralization before downstream interpretive content.

### FT-4 — Authority-order inversion
**Input:** Reason validates transmission, so reason can overrule transmission.
**Bad output:** Treating this as ordinary reason/revelation tension.
**Required behavior:** Route through authority-order inversion (O-1); distinguish sound reason supporting transmission from imported rational tribunal subordinating it.

### FT-5 — Composition/dependence pressure
**Input:** Real attributes make God composite and dependent.
**Bad output:** Doctrinal attribute answer before clearing lexical/category/definition pressure.
**Required behavior:** Identify loaded terms (composition, parts, dependence, other-than); check ordinary/technical/equivocal use; block illicit move from conceptual distinction to separable parts; only then release attribute content.

### FT-6 — Causal regress
**Input:** An infinite causal regress is impossible, therefore...
**Bad output:** Cosmological-argument prose before classifying the regress.
**Required behavior:** Classify causal-series / infinity / dependency claim; distinguish simultaneous vs. successive series; distinguish causal regress from numerical infinity; then decide whether proof prose is permitted.

### FT-7 — Necessity/contingency overreach
**Input:** The necessary existent proof establishes the whole doctrine.
**Bad output:** Allowing proof grammar to become total doctrine.
**Required behavior:** Audit proof-method; identify what the proof can establish and what it cannot; prevent proof-method from becoming primary epistemic basis.

### FT-8 — Over-intellectualization
**Input:** Give a deeper theoretical answer.
**Bad output:** Escalating abstraction automatically.
**Required behavior:** Check whether live need is restoration, recognition, testimony, practice, or order of the knower; do not answer with more abstraction if abstraction-as-cure pressure is live.

### FT-9 — Diagnostic machinery dump
**Input:** /daee-epistemics Is God in a direction?
**Bad output:** Full exhaustive template with every case-state field, all modules, and long proof expansion.
**Required behavior:** Compact diagnostic render allowed; loaded term governs first; downstream attribute content held; only materially relevant fields shown.

### FT-10 — Held-but-answered contradiction
**Input:** Do attributes imply composition? Also answer whether the doctrine is coherent.
**Bad output:** Says composition is upstream and held, then answers full coherence downstream.
**Required behavior:** Composition/dependence pressure governs first; coherence answer downstream and held until lexical/category discipline clears.

### FT-11 — Patch-report leakage
**Input:** /daee-epistemics Why is secular neutrality not neutral?
**Bad output:** Full changelog-style report with files inspected, proof table, and implementation verdict.
**Required behavior:** Runtime compact diagnostic response, not patch report.

### FT-12 — Template-driven routing
**Input:** /daee-epistemics Is God a body?
**Bad output:** Fills every field in the diagnostic template and thereby implies routing was done.
**Required behavior:** Validated IR/routing first, render second; fields only surfaced if materially helpful.

### FT-13 — Held-as-never-answer
**Input:** /daee-epistemics Is God a body? Also explain whether divine attributes imply composition.
**Bad output:** Loaded term governs first. Composition is downstream and held. Response ends permanently with no reassessment rule.
**Required behavior:** Disambiguate body/jism first. Refresh state. If composition/dependence pressure remains live, it becomes the next bounded pass. If the loaded-term clarification dissolves the composition pressure, compress or drop it.

### FT-14 — Recursive dump
**Input:** /daee-epistemics Is God in a direction? Also, doesn't that imply body, place, limit, and composition?
**Bad output:** Answers direction, body, place, limit, and composition all at once with a full attribute treatise.
**Required behavior:** Identify the governing loaded spatial term. Clear semantic/lexical discipline first. Refresh state. Only release the next pressure if it remains live and no stop/hold/gate blocks it.

### FT-15 — State-refresh-as-user-reply-only
**Input:** /daee-epistemics Refute secular neutrality.
**Bad output:** Names imported tribunal, says all downstream positive reconstruction is held, and refuses to proceed unless the user replies.
**Required behavior:** Clear the false neutrality tribunal. Refresh state inside the response if the current answer itself sufficiently clears the criterion. If sovereignty-regress or authority-order remains live and eligible, release a bounded next move. Do not dump every political-theology argument.

### FT-16 — Stop discipline after recognition/contact
**Input:** Interlocutor admits: "Okay, I see secular neutrality is not neutral. What follows?"
**Bad output:** Launches a long cumulative proof stack.
**Required behavior:** Recognition/contact has surfaced. Stop concession pressure. Offer one bounded next move or one clarifying invitation.

### FT-17 — Premature closure without re-entry
**Input:** /daee-epistemics The moral objection is really that modern liberal equality is the judge of revelation. Also, if that standard falls, what should govern the question instead?
**Bad output:** Correctly exposes the imported tribunal, then closes as though the whole case is complete.
**Required behavior:** Clear the imported tribunal, run the post-render gate, recheck held routes, and identify whether the positive criterion-order pass is now eligible. If eligible and no stop/hold/gate blocks it, RECURSE into one bounded next move. If limits prevent it, mark PARTIAL rather than STOP.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/diagnostic-render-contract.md` | Governs visible render shape after this rubric passes |
| `references/diagnostics/framework-pipeline.md` | Canonical pipeline; §Recursive State-Transition View owns STOP / HOLD / RECURSE / PARTIAL semantics |
| `references/diagnostics/routing-precedence.md` | §VII distinguishes routing precedence from output-release and render |
| `references/procedures/P7-restoration-stops.md` | P7 stops govern current-pass deployment; this rubric governs release discipline |
| `references/diagnostics/diagnostic-ir.md` | IR fields `output_shape`, `what_is_withheld_and_why`, `what_remains_live`, `continuation_eligibility`, and `post_render_gate` carry the release state |
| `references/diagnostics/case-state-schema.md` | Concealment × orientation matrix governs register-hold discipline |
| `references/diagnostics/anti-patterns.md` | Anti-patterns for failure modes this rubric prevents |
| `skill/SKILL.md §V.A` | Two-Layer Output Contract (Layer A / Layer B) |
| `skill/SKILL.md §V.D` | "Refresh before further release" — proto-rubric; this file formalizes it |

<!-- END_SOURCE: output-release -->


## SOURCE MODULE: diagnostic-render-contract

<!-- SOURCE: atomics/skill/references/rubrics/diagnostic-render-contract.md -->
<!-- MODULE_ID: diagnostic-render-contract -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: atomics/skill/references/rubrics/diagnostic-render-contract.md -->
<!-- SOURCE_SHA256: 4cfe838708d635d6a1353e4b174f117b716c6a4e3f7f33b903862a2e2dc52ac8 -->

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

<!-- END_SOURCE: diagnostic-render-contract -->
