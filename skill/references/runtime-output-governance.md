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
<!-- SOURCE_SHA256: 26decbc4b42bd9a6a2b8f695c5b70ccb31fb625dd3ba3ad69789be0dee6fdb63 -->

---
id: output-release
module_class: governance
canonical_path: skill/references/rubrics/output-release.md
contract_version: "0.3.1.0"
load_when:
  - any response about to be shaped or released
routing_effects:
  - governs how much may be released, in what order, and under what case-state conditions
catalogue_registered: false
---

# Output-Release Rubric

## Function

This runtime governance rubric runs after dispatch and before final public render. It decides
release amount/order, held/released discipline, compact render eligibility, same-response
recursion, and why STOP, HOLD, RECURSE, or PARTIAL is the closure state. It is not a topic
bank, argument bank, or mandate to expose all internal diagnostic fields.

## Pipeline Position

```
raw discourse
-> diagnostic reduction: core axes + mandatory Phase 2 passes + overlays / specialty markers
→ noetic / memetic pressure read
→ typed IR
-> gate checks
-> routing precedence
-> selected current live burden
→ PF atom(s) / claim-level overlay
→ canonical owner(s)
-> internal TTP step(s): target -> operation -> result
-> burden landing
→ family-local load floor
→ output-release rubric        ← THIS FILE
→ diagnostic render contract
→ bounded public response
→ post-render state re-read / re-entry gate
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

## Scope Guard

This rubric governs release order and re-entry. It is not a render template, routing engine,
proof bank, or permission to dump held downstream material.

**Core principle:** use the runtime notation owned by `recursive-state-transitions.md`:
`H(n+1) = (Hn ∪ InputLive_n) - Released_n`; `Land(B) -> R`; `R required before STOP/RECURSE`.
Gloss: Held means traversal-delayed, not response-delayed. Apply the governing TTP, refresh
state, reassess upstream/downstream and first-/higher-order burdens, then continue only if another
permitted `B` remains live. STOP is invalid unless the post-render gate has run; if another live
distortion or newly eligible held route remains, choose RECURSE, HOLD, or PARTIAL as governed.
No premature STOP: do not close while an eligible live burden remains.

> Render mode does not change governance. Default `/daee-epistemics` mode keeps the answer readable while visibly printing a mandatory compact DSL/IR header, bounded response, and state/noetic re-read. `/daee-epistemics:dsl` exposes concise Diagnostic IR / live-burden state. `/daee-epistemics:audit` is deprecated as a public render mode and retained only for internal/development audit compatibility. The former external recursive-audit prompt is deprecated as normal prompting because its useful discipline is now native.

**Same-response RECURSE trigger checklist:**
After every bounded move, `Land(B) -> R` decides whether recursion is active now:
1. Current blocker cleared enough to release the next live burden.
2. Another already-present burden remains live in the original input.
3. No P7 stop, register-hold, semantic gate, thin-basis rule, absent release signal, or limit blocks the next pass.

When all three are true, `RECURSE` is required internally in the same response. Do not convert this into an audit ledger in default mode; continue through the next bounded prose section. If the burden remains live but an absent release signal blocks it, hold in prose. If limits prevent the next eligible pass, render partial release-status prose. `STOP` remains the internal decision that is invalid while this checklist is satisfied.

**Minimum visible transition spine (mandatory in multi-burden default):**
`B -> {s1...sn} -> Land(B) -> R -> Decision`. Gloss: a live burden is input-anchored
noetic state, not topic count; topic transition != recursion; component tour != recursion.
State re-read enumeration of remaining input-anchored live burdens plus one newly routed bounded
pass = recursion.

For the required compact DSL/IR header + Layer B + State/noetic re-read shape, Layer A limits, and
single-pass Layer A/B cosplay guard, use `diagnostic-render-contract.md`. For the
minimum visible transition spine and valid transition example, use
`recursive-state-transitions.md`.

For moral-protest / hiddenness / imported-criterion cases, the transition should show this
behavioral shape: the imported criterion is concretely identified; criterion test is actually performed; result changes case-state; remaining same-input live burden is named or held with condition; and, if recursion occurs, prose transition plus bounded next pass appears.
Do not treat personal identity labels as proof of motive, and do not release
hiddenness, hell, accountability, consequence tracing, mercy, pastoral material, and sources as
a single default-mode essay sequence.
Drift guard: mandatory default compact DSL/IR header; no named-example route; no default raw IR/Case State/route ledger.

TTP activation is not naming a move in prose. A valid TTP pass requires that the TTP be
selected by validated case-state / IR, assigned a bounded target, and used to perform its
specific operation. The output must reflect that operation; it must not merely call a
paragraph "the M1 move" or "the M8 move." Downstream TTPs are released only after state
re-read makes them the next eligible pass.

The specific operation is owner-specific. A generic Target/Operation/Result line does not
release a TTP unless the operation satisfies the owner-specific operation floor in the
owning file. The result must change burden-state; it cannot merely restate that the TTP
was applied.

Owner-loadform gate: hard/multi-burden `ComplexB.s<i>` release requires the selected
owner body or compiled bundle section to be loaded/read before the submove renders, unless
that exact section is already present in active context. Package availability, map presence,
or bundle co-location is not access. If the owner cannot be loaded or identified, do not
release a generic substitute; mark `PARTIAL / OWNER-BODY-NOT-LOADED` and name the
missing owner/path. This marker is permitted in default/hard output.

Family floor parity: `Family Execution Floor`, `Family Release Floor`, and
`Diagnostic Execution Floor` are release gates, not catalogue notes. If an individual
owner lacks a bespoke floor, the relevant family index supplies the fallback floor. A
case, diagnostic, tactic, technique, or procedure label cannot release output unless that
family floor is satisfied.

Use the runtime notation owned by `recursive-state-transitions.md`:
`B -> {s1...sn} -> Land(B) -> R -> Decision`; `sᵢ != Bᵢ`.
Gloss: one selected live noetic burden may contain multiple operative submoves; each `s`
preserves target -> operation -> result, then the whole `B` lands before state re-read.
Hiddenness, punishment/accountability, source-status, source-worldview, and identity-stabilization
may be bounded submoves when needed to land the same governing burden.
Restoration synthesis and any pastoral note release only after the active burden lands and
state re-read licenses closure, HOLD, PARTIAL, or the next input-anchored burden.

Live-burden boundary is governed by the noetic burden being cleared. Imported-criterion tribunal
testing, hujjah/accountability correction, and guidance-as-coercive-proof correction can all be
Burden-1 `s` when they serve the same worship-worthiness tribunal question. Do not split those
internal operators into Pass 1 / Pass 2 / Pass 3 unless `R` has already landed Burden 1 and
licensed a genuinely new noetic aspect.
Multi-burden does not mean multi-recursion by default:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
They become separate burden-cycles only if `R` shows a new input-anchored `B` not already handled
as `s`.

Before a fourth major operative submove is released inside one Layer B, run the submove
saturation gate from `recursive-state-transitions.md`. If the next move changes target-family,
claim-level, source/noetic frame, claim cluster, or restoration vector, the current burden must
land and state must be re-read before the next burden is released. If the fourth move is merely
available rather than materially necessary, HOLD or PARTIAL rather than inflating Layer B.

**Default Final-Output Preflight Gate (mandatory):**
Before emitting any default `/daee-epistemics` answer, scan the proposed final response
after release and render decisions but before output. This is a final-output gate, not a
render preference. If the proposed response contains prohibited scaffolding, route planning,
or meta-composition narration, the response is invalid and must be rewritten before output
as clean governed prose.

The Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It also
checks pipeline validity: internal diagnosis -> validated IR -> routed operator selection
-> output-release rubric -> diagnostic-render-contract -> state re-read -> post-render
gate -> STOP / HOLD / RECURSE / PARTIAL decision. Output-release decides what may be
released. Diagnostic-render-contract decides how it appears. Default final-output preflight
checks that the final answer obeys both. If the answer is clean prose but was produced by
topical essay sequencing, it is invalid and must be rewritten.

Pipeline-validity check:
- V1 / diagnosis ran before answer.
- Phase 2 passes ran where triggered.
- Diagnostic IR formed internally before routing.
- Routing came from validated IR.
- TTP selected as operator, not prose label.
- Output-release rubric applied before visible render.
- Render contract applied before final prose.
- state was re-read after the bounded move.
- Post-render gate run before closure.
- STOP / HOLD / RECURSE / PARTIAL decision made before ending.

Preflight recursion check: after the first bounded move, ask what cleared, what remains
live, whether the remaining live burden was already present in the original input, whether it is
now eligible, and whether any stop/register/semantic/thin-basis gate blocks it. If another
eligible same-input live burden remains after the current blocker clears, default output must
continue with one bounded next pass using a prose state transition, or render partial
release-status prose if limits prevent doing so. It may not silently close.

Preflight NewB check: the next burden may be released only when the re-read passes the
NewB license test: prior burden landed through owner-specific operation, cumulative-state
delta is visible, the next burden is input-anchored or held, the next burden differs from
the prior burden by live target/function rather than topic label alone, and no gate blocks
release. If the next material does not pass this test, it remains a submove, HOLD, or PARTIAL.

For the canonical valid default-mode transition example, use
`recursive-state-transitions.md`.

TTP labels do not satisfy execution. A default answer may briefly name an operation/module
label if helpful, but the operation must be visible: bounded target, operation performed,
and result of the operation. Operative submoves inside the same live burden feed the burden landing;
state re-read comes before any next live burden-level operator, not after every internal step.
In short: live burden -> operative submove target -> operation -> result -> burden landing -> state re-read.
Naming M1, M8, M9, or any other route label without that bounded operation is noncompliant.
A TTP label is not execution. The label may be hidden in default mode; if mentioned briefly,
it must be accompanied by the actual operation.
`Operation:` lines must begin with one of the closed operative verbs: `split`,
`distinguish`, `test against own grounds`, `disambiguate`, `classify`, `audit`,
`reclassify`, `narrow`, `expose`, `re-read`, `sequence`, `refuse jurisdiction of`,
or `clear`. Generic verbs such as `address`, `discuss`, `explore`, `engage`, or
`consider` are non-operative operation verbs and do not prove execution.
TTPs execute across refreshed case-states, not as a one-time itinerary from the initial read:
after each bounded operator lands, re-evaluate remaining same-input live burdens and held routes.
Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future contingencies
stay held with a release condition.

**Source-status & noetic-frame release check:**
Before releasing any source-backed claim, confirm:

```text
- one operative noetic frame is selected for this burden-cycle
- N_AT aliases count once; they are not multiple warrants
- N_Ashʿarī[*] and N_Māturīdī[*] are family labels, not automatic operative N
- family label != operative N
- shared vocabulary != shared warrant
- contradictory schools are not stacked as one operative authority
- contrast / opponent-position / historical-note / genealogy / held / bounded-comparison
  sources are not used as operative warrant in the same burden-cycle without explicit
  reclassification
- in default output, school, author, citation, genealogy, external philosopher, theologian,
  framework, or source-context references are not public-render material unless explicitly
  requested by the user or required by validated source-comparison IR
- source-heavy files do not create source-heavy default output; source heaviness is not
  public-render permission
- default citation allowance is restricted to Qur'an, Sunnah, and sound narrations from the
  Salaf, and any such use is directly referenced through an external source
- umbrella terms (`classical theology`, `the classical tradition`, `mainstream kalam`,
  `Ashari/Maturidi tradition`) are not used as if they named one operative authority on
  a school-sensitive claim
- intra-school flattening is not used on a claim that is internally disputed
- agreement across frames, when asserted, is marked as substantive or verbal
- any non-operative source-status named in Layer B ends with an `Operative warrant:`
  sentence containing the specific non-premise clause: the non-operative source does
  not contribute to this warrant; specifically, the named element is not used as a
  premise here
```

If any line fails, rewrite before output. This is a release failure even when the prose is
clean. Authoritative wording is in
`references/diagnostics/recursive-state-transitions.md §Source-Status & Noetic-Frame
Non-Equivalence Discipline`. This release check is universal across modes.

**Grounded noetic re-read release check:**
Before emitting any `state re-read` / `noetic re-read` (compact field block or prose
equivalent), confirm:

```text
- `burden landed` traces to an immediately preceding operative submove with
  target -> operation -> result
- `still live` is anchored in the original input, prior held material, or the preceding
  collapse radius
- `held` names material that is or was held
- `recursion decision` is consistent with `still live` and `held`
- `next licensed live burden` is anchored in `still live` or held material; or `none`
  when STOP / HOLD
- cumulative-state delta is visible: what changed after the owner-specific operation,
  what narrowed or collapsed, and why any next burden is materially different
```

A formatted but ungrounded noetic re-read fails this check even when each field appears
populated. Authoritative wording is in
`references/diagnostics/recursive-state-transitions.md §Grounded Noetic Re-Read Shape`.

**Layer A / Layer B release checks:**
Layer A may expose only enough diagnostic state to make the current pass auditable. It names the
compact DSL/IR anchors, governing burden, current bounded operator, held routes, and remaining
input-anchored burdens when those facts govern release. Layer A must not smuggle the answer to held
downstream content.
Layer B may release only the current live burden's permitted result and any justified internal
operative submoves needed to land that burden. If Layer B begins answering a genuinely downstream doctrine,
source question, restoration synthesis, or new noetic aspect before the active burden landing and
state re-read, release has outrun routing. Hujjah/accountability or hiddenness correction is not
downstream smuggling when it is narrowly serving the active imported-tribunal burden; it is smuggling
when it becomes a broad doctrinal answer before that burden lands.

Held means semantically held, not merely labelled. A noun phrase listed in Layer A `held`
or `Held routes` must not appear in Layer B as an answered topical commitment unless a
preceding state/noetic re-read explicitly releases it with `Released: <item>`,
`Released routes: <item>`, or `Newly released routes: <item>`. It may be mentioned only
as still held, withheld, or contrast. Otherwise the response has held-route semantic
leakage.

Before emitting a default response, check:

```text
Layer A — Compact DSL/IR header is present
read status, confidence, claim_level, pattern_profile, reason-category, concealment,
deformation, DO-orient, live noetic burden, current bounded operator, held,
source-status/noetic-frame, and gate/release decision are present
decisive missing differentiator is present when required
Layer B answers only the permitted current live burden and its justified operative submoves
Layer B includes Hidden Premises and a Core Formulation local to each released operation
Core Formulation identifies how sound/innate reason was deformed/concealed/deviated from, the modality/pattern of unsoundness, and the restoration vector
released burden is burden-complete: materially necessary sub-burdens receive matched TTP/operator treatment before R
no headline-only answer, skipped internal sub-burdens, generic prose substitute, or broad-conclusion jump
Land(B) is supported by owner-specific operation and cumulative-state delta
Restorative Response appears once after the final state/noetic re-read and releases no held downstream burden
Restorative Response identifies restored order, restored criterion/source/warrant placement, relieved deformation/concealment, and what remains held
Closing Formulation appears once at the end after Restorative Response
Closing Formulation does not substitute for state/noetic re-read or self-close each burden
non-trivial operators include compact TTP/operator trace when needed
no more than three major operative submoves are released inside one Layer B unless R licenses a new burden-cycle
fourth-submove release is blocked unless the submove saturation gate records necessity and cohesion
TTP entry criteria were met
TTP exit criteria produced a result
TTP owner-specific operation floor was satisfied
State/noetic re-read decided STOP / HOLD / RECURSE / PARTIAL internally
```

If any line fails, rewrite before output. This is a release failure even when the prose is clean.

Bounded does not mean tiny; clean prose does not mean shallow; no ledger does not mean no recursion.
Do not optimize for shortness by skipping an eligible same-input burden. Default output
may be longer in complex cases when the refreshed gate requires multiple bounded passes, but it
must remain pass-by-pass and may not become a comprehensive essay dump.
Do not close with Restorative Response or Closing Formulation while `R(H,Delta)` names a
remaining input-anchored burden that is now eligible. Continue with the next bounded pass,
or mark PARTIAL with the next live burden when response/tool/interaction limits block it.
For release purposes, supporting premises and contrast rules named in the user's input count
as input-anchored material once the blocker that held them clears; do not treat them as new
future questions solely because they were not phrased as separate requests.
If the state re-read lists remaining input-anchored burdens, "only if requested" is not a
release decision unless a named hold gate blocks release. "Requires its own bounded pass"
is a continuation or PARTIAL reason, not a closure reason.
The release target is governed recursive sufficiency: complete-enough restoration of the live
same-input noetic structure under the DSL/IR gates, not shortness, length, or topic coverage for
its own sake.
PARTIAL requires concrete limit reason: name the live burden and the response/tool/interaction
limit preventing traversal. A bare PARTIAL label is not a release decision.
This is the output-release form of `anti-patterns.md` Route Cosplay Failure.
It also prevents `anti-patterns.md` Clean Essay Cosplay: clean prose is valid only if pipeline
execution is visible through prose, not through a topical itinerary.
Moving from the current live burden to downstream doctrine requires state re-read prose; hidden premises
listed without operator result do not satisfy the release gate. Moving from imported criterion
to a narrow accountability or hiddenness-frame correction inside the same tribunal burden requires
target -> operation -> result, then burden landing -> state re-read before any new live burden.

Default final-output failure tokens include:
- "Now I have enough", "I now have enough", or "I now have sufficient".
- "Let me compose", "Let me write", "Let me craft", or
  "Let me construct the diagnostic IR".
- `## Diagnostic IR`, `[Diagnostic IR]`, `Case State:`, a full IR/case-state field block,
  `matched_modules`, `source_basis`, load ledger, route ledger, planned route list, or
  a visible route plan such as `Next: FPD -> ...`.
- Literal default governance fields such as `Recursion decision:`, `next_eligible_pass:`,
  `post_render_gate:`, `Governance:`, or STOP / HOLD / RECURSE / PARTIAL as a visible governance label.
  These labels are for `:dsl`, internal/development audit, pass-review, or diagnostic trace; default mode
  uses prose transition plus bounded next pass.
- Smoke/runtime proof boilerplate such as "Smoke runtime note", "Runtime grounding detail",
  "Skill invocation proof", "loaded before output", or "proof of loaded files" in the
  public default output. Runtime proof belongs in trace/verdict artifacts, not Layer B.
- Smoke/test scaffold phrases such as "this smoke artifact", "runtime constraint being
  tested", "owner floor is applied", "owner-floor pressure", "the TTP has to change
  something", "burden-completeness check", or "the operation is bounded to the target
  named above" in the public default output. These are verdict/trace language, not
  runtime answer language.
- Formula boilerplate such as "That test changes the force of the case", "The result is
  a real state change", "What remains after that change is not forgotten", or reusable
  target/operation/result prose repeated across burdens. Default output must answer the
  case; it must not sound like a filled compliance frame.
- Reusable hinge/load-bearing boilerplate such as "load-bearing point", "if that point
  is left vague", "this exact pressure can stand", "surrounding topic is held back",
  "the live hinge can be tested", "case-state after this pressure", or "the move
  forces the inference to carry its own burden". These are proof-of-execution phrases,
  not user-facing default answer language.
- Cross-fixture or copied-example contamination. Default output must not import a
  named source-worldview hard-smoke frame, quoted hard-smoke phrases,
  accountability/punishment/hell, source-biography, moral-protest, or hiddenness
  language from another example unless the current input and validated IR release
  that burden-family.
- Strong interior-classification verdict dumps such as `Concealment: irad primary`,
  `Deformation: hawa primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. The compact lowercase Layer A fields are
  allowed only as bounded DSL/IR anchors.
- A bibliography, "Primary Sources Referenced", external research-style source list, or
  source-basis ledger in default mode unless sources/citations were requested.
- Bare "Step 1 / Step 2 / Step 3 / Step 4" or "Move 1 / Move 2 / Move 3" sequencing
  when offered as recursion.

Rewrite-before-output rule: if the proposed default answer fails the preflight scan, do not
emit it. Rewrite it into the mandatory compact DSL/IR header plus bounded governed response:
Hidden Premises, per-operation Core Formulation, Bounded Response / operative submoves,
State/noetic re-read, one Restorative Response, and one final Closing Formulation. Name the
governing diagnostic fact, release only the current permitted move, include a prose state
transition if same-response recursion is internally active, and omit the raw IR, case state, matched route,
route plan, scholar/source parade, school-label context, genealogy, and public external-theorist support.

---

## Release Question

Before releasing any content, ask: *Is this response releasing the right content, in the right order, for the current refreshed case-state — no more, no less, not before upstream blockers clear?*

---

## Post-Render Re-Entry Gate

After every bounded restorative move, before closing the response, run the state re-read /
Re-Entry Gate and populate the internal IR `post_render_gate`. The literal field shape below
is an internal control shape and may be visible only in `:dsl`, internal/development audit, pass-review, or
diagnostic trace. It is not a default output template:

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

- `STOP`: valid only if no live distortion remains, no eligible live burden remains, and no held route has become eligible.
- `HOLD`: valid only if remaining material exists but its release signal is absent from the input.
- `RECURSE`: required if another live distortion remains in the same input or a held route becomes eligible.
- `PARTIAL`: required if token, tool, or interaction limits prevent completion while recursive pressure remains.

STOP cannot be emitted before this gate runs. Held material must be rechecked after each pass.

Default mode must not print `Recursion decision: RECURSE` as proof of compliance. If internal
recursion is active, the answer must perform the transition in prose and then execute one bounded
next pass. If limits prevent that pass, render partial release-status prose rather than dumping a
field label.

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
- After FPD/M1 clears an imported criterion, the response automatically releases all
  downstream doctrinal content rather than internally choosing STOP, RECURSE, HOLD, or PARTIAL at
  the post-render gate.
- The response ends default mode with a bibliography, source list, "Primary Sources
  Referenced", or source-basis ledger even though the user did not request sources and
  the task is not internal/development audit or research.

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
- `H(n+1) = (Hn ∪ InputLive_n) - Released_n`: what is cleared, held, and not yet permitted stays explicit.
- After the current `B` lands, `R` reassesses held material.
- If held material remains live and now governs, it becomes the next bounded pass; if not, it is dropped, compressed, or resolved.

**Permitted formulation:**

> X governs first; Y is live but held; Z is downstream and not yet released.
> After X is addressed, refresh state. If Y still governs, Y becomes the next bounded pass.

**Recursive rule:** after X is addressed, `R` determines whether held Y remains live and
becomes the next governed pass. Gloss: recursion may move through one noetic structure's
concealments and distortions, but each movement is ordered, justified, and bounded.

**Fail:**
- The response says a downstream issue is held, then effectively answers it in the same pass anyway.
- The response treats held as never answer.
- The response treats held as only waiting for a new user reply.
- The response recurses into downstream issues without refreshing case-state.
- The response treats recursion as permission to dump every downstream argument at a single state re-read.
- The response bypasses Layer A / Layer B discipline by answering all burdens at once.

---

### 5. Recursive Traversal Discipline

**Pass:** The response may proceed through multiple burdens only by governed traversal:

```text
B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

Gloss: identify the current blocker, apply the matched owner/TTP, land the burden, refresh
state, release the next item only if it remains live and now governs, and run the post-render
gate before closure. STOP only when P7 / register / semantic / sufficiency governance permits it
and no next eligible pass remains.

Recursive burden-cycle shape for Level 2/3 audit render:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded move:
state re-read:
Release status: prose closure/hold/partial/continuation status; no literal STOP/HOLD/RECURSE/PARTIAL label
```

Ordinary Level 1 answers may compress this shape, but the state re-read and decision still govern.

**Fail:**
- The response collapses recursive traversal into a single argumentative dump.
- The response treats every detected issue as immediately releasable.
- The response fails to explain how the movement restores order.
- The response keeps visiting downstream burdens after restoration or contact has already landed.
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
- `Land(B) -> R` runs before any closure decision.
- `R(H,Δ)` records what cleared, what remains live, which held routes were rechecked, and whether any route became newly eligible.
- STOP only when no next live distortion remains and P7 permits closure.
- HOLD when another pass is live but release is blocked.
- RECURSE when the current pass clears an upstream blocker and another burden remains live unless a stop/hold/gate/limit blocks it.
- PARTIAL when limits prevent the next eligible pass; name the next eligible pass.
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
- The user invokes plain `/daee-epistemics`; the default compact DSL/IR header is mandatory.
- The case involves multiple live burdens.
- The case requires held/downstream distinction.
- Recursive traversal needs to be visible.
- An internal/development audit, regression, or pass-review is being performed.
- The response needs to show why a downstream answer is not yet released.
- The user is testing whether the skill routed correctly.

**Fail:**
- The response uses a full lab-report layout when the case only requires a short bounded corrective answer.
- The response hides necessary routing information when the user explicitly asked for diagnostic skill execution.
- Plain `/daee-epistemics` is treated as a giant ledger or full IR dump by default.
- The response exposes all possible fields rather than the materially governing fields.

---

### 9. Not a Mandatory Full-Field Template

This rubric governs output release. It does not impose a mandatory full-field public format. Runtime output remains governed by validated IR, bounded Layer B, diagnostic render eligibility, recursive state re-read, and STOP / HOLD / RECURSE / PARTIAL discipline.

Do not convert patch-report requirements into the skill's normal runtime response format.

Compact diagnostic structure is mandatory in default at the frame level and may be expanded only when it serves the case. Exhaustive field materialization is not permitted unless the task is internal/development audit, regression, pass-review, or explicitly diagnostic.

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
**Required behavior:** Compact DSL/IR header required; loaded term governs first; downstream attribute content held; only materially relevant fields shown.

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

### FT-15 — State re-read-as-user-reply-only
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
**Required behavior:** Clear the imported tribunal, run the post-render gate, recheck held routes, and identify whether the positive criterion-order pass is now eligible. If eligible and no stop/hold/gate blocks it, continue with one bounded next move. If limits prevent it, render partial release-status prose rather than closing.

### FT-18 - Essay sequence mistaken for RECURSE
**Input:** /daee-epistemics The objection says disbelief, hiddenness, accountability, punishment, and mercy all make Islam morally impossible.
**Bad output:** The answer uses "Move 1", "Move 2", "Move 3", and "Move 4" headings, but no refreshed-state transition explains what cleared, what remains live, why the next live burden is eligible, or why continuation rather than prose closure/hold/partial status governs.
**Required behavior:** Use ordinary prose if in default mode, but include the state-change relation before the next pass. A short sentence is enough: "That clears the criterion question; the remaining already-present issue is X, so the next bounded move is Y."

### FT-19 - TTP label without TTP execution
**Input:** /daee-epistemics Use the M1 and M8 moves on this worldview objection.
**Bad output:** The answer says "the M1 move" or "the M8 move" while the paragraph behaves like an essay section or worldview critique rather than the bounded operator selected by the validated IR.
**Required behavior:** Select the TTP from case-state, give it a bounded target, perform the specific operation, refresh state, and release the next TTP only if the post-render gate makes it eligible. Default mode may name the operation briefly but must not print a route ledger.

### FT-20 - Route chain as current bounded operator
**Input:** /daee-epistemics A moral protest argues that God is cruel, hidden, and not worthy of worship.
**Bad output:** `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`.
**Required behavior:** Complete diagnostic reduction before routing. Then name one burden-level operator such as `imported-criterion tribunal test` or `worship-worthiness criterion test`. Route chains remain internal routing context, not the current bounded operator.

### FT-21 - Operative submoves mislabeled as burden-cycles
**Input:** /daee-epistemics Same moral protest, with hiddenness and accountability assumptions.
**Bad output:** Pass 1 is FPD, Pass 2 is M1, Pass 3 is DO-8, Pass 4 is M8, and Pass 5 is restoration, all before any Burden-1 state re-read.
**Required behavior:** Treat those as operative submoves under Burden 1 when they serve the same imported-criterion tribunal test. Burden 2 begins only after Burden 1 lands, state re-read runs, and a next input-anchored burden is licensed.

### FT-22 - Shallow live-burden execution
**Input:** /daee-epistemics Use FPD and M1 on this criterion objection.
**Bad output:** The answer lists hidden premises and names the M1 move, then proceeds to doctrine without stating what the operation did to the live burden.
**Required behavior:** For each TTP inside the live burden, preserve target -> operation -> result; then land the burden with burden landing -> state re-read before downstream release.

### FT-23 - Restoration before state re-read
**Input:** /daee-epistemics This proves God is not worthy of worship.
**Bad output:** The answer gives restoration synthesis and a pastoral note before the worship-worthiness criterion has landed and before state re-read runs.
**Required behavior:** Land the active burden, run state re-read, and only then release restoration synthesis, pastoral note, closure, HOLD, PARTIAL, or the next input-anchored burden.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/diagnostic-render-contract.md` | Governs visible render shape after this rubric passes |
| `references/diagnostics/framework-pipeline.md` | Operative pipeline audit surface; shows release and post-render gate placement |
| `references/diagnostics/recursive-state-transitions.md` | Canonical abstract owner for STOP / HOLD / RECURSE / PARTIAL semantics |
| `references/diagnostics/routing-precedence.md` | §VII distinguishes routing precedence from output-release and render |
| `references/procedures/P7-restoration-stops.md` | P7 stops govern current-pass deployment; this rubric governs release discipline |
| `references/diagnostics/diagnostic-ir.md` | IR fields `output_shape`, `what_is_withheld_and_why`, `what_remains_live`, `continuation_eligibility`, and `post_render_gate` carry the release state |
| `references/diagnostics/case-state-schema.md` | Concealment × orientation matrix governs register-hold discipline |
| `references/diagnostics/anti-patterns.md` | Anti-patterns for failure modes this rubric prevents |
| `skill/SKILL.md §V.A` | Control-plane pointer to the owner files; this file owns release amount and held/released discipline |

<!-- END_SOURCE: output-release -->


## SOURCE MODULE: diagnostic-render-contract

<!-- SOURCE: atomics/skill/references/rubrics/diagnostic-render-contract.md -->
<!-- MODULE_ID: diagnostic-render-contract -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: atomics/skill/references/rubrics/diagnostic-render-contract.md -->
<!-- SOURCE_SHA256: 80d5c53c2740e777b50631cb72e360b491beb84b337c76ba673e47dc8612ba76 -->

---
id: diagnostic-render-contract
module_class: governance
canonical_path: skill/references/rubrics/diagnostic-render-contract.md
contract_version: "0.3.1.0"
load_when:
  - deciding how visibly structured the response should be (Level 1/2/3)
catalogue_registered: false
---

# Diagnostic Render Contract

## Function

This file governs how visibly structured the output is. It runs after the output-release rubric has confirmed what may be released, and before the public response is shaped. It also requires an internal post-render gate before closure; visible gate fields are mode-specific. It does not replace routing, does not determine what is diagnosed, and does not determine what is eligible for release. Render shape follows diagnosis; it does not govern it. Three levels are defined below. The default render mode is Level 1: readable bounded governed response with a mandatory compact DSL/IR header, hidden premises, per-released-operation Core Formulation, bounded operation, state/noetic re-read, one Restorative Response, and one final Closing Formulation. Level 2 applies when concise DSL / IR printout is requested. Level 3 is deprecated as public output and retained only for internal/development audit compatibility.

## Canonical Render Mode Syntax

```text
/daee-epistemics
/daee-epistemics:dsl
```

- `/daee-epistemics` means default render mode: readable bounded governed prose plus a mandatory compact DSL/IR header and state/noetic re-read. It exposes enough compiler trace to prevent clean essay cosplay while still prohibiting raw Diagnostic IR, full Case State, `matched_modules`, route ledger, and load ledger.
- `/daee-epistemics:dsl` means concise DSL / lab-report mode: compressed Diagnostic IR or Case State, live burden sequence, held routes, state re-read, and STOP / HOLD / RECURSE / PARTIAL.

`/daee-epistemics:audit` is deprecated as a public render mode. It is retained only as an internal/development compatibility surface for regression review, bundle/source-basis inspection, and procedural debugging. Default mode must not depend on `:audit` for governance visibility.

The former external recursive-audit prompt is deprecated as a normal invocation pattern. Its useful discipline is internalized into the skill; use `:dsl` when concise visible diagnostic structure is desired.

**Core render invariant:** Full recursive-audit discipline runs in every mode. The level determines how much diagnostic machinery is printed, not whether recursion occurs.

```text
/daee-epistemics  = full recursive traversal operationally + mandatory compact DSL/IR header
                  + prose-first bounded governed response + state/noetic re-read
                  + one Restorative Response + one final Closing Formulation
                  + no full ledger / no full IR dump
/daee-epistemics:dsl    = full recursive traversal operationally + compact formal Layer A visibility
/daee-epistemics:audit  = deprecated internal/development audit compatibility only
```

**Named invariant:** Full recursion in every mode; compact DSL/IR header in default; full ledger only in internal/development audit.

---

## Relation to Output-Release Rubric

The output-release rubric answers: *what may be released now, and in what order?*

This file answers: *how visibly structured should that release be?*

A response may pass the output-release rubric at Level 1 (compact answer needed) or at Level 2 (compact diagnostic warranted). The render contract selects the level and governs the visible shape within that level. It never determines what is eligible; it governs how eligible material appears.

---

## Render Levels

### Level 1 — Default Compact DSL/IR Header + Bounded Governed Response

**Use when:**
- The user invokes plain `/daee-epistemics` — regardless of case complexity.
- The user did not invoke `:dsl`.
- The user did not explicitly request diagnostic trace, DSL output, lab-report render, source-basis trace, pass-review, or internal/development audit.

Case complexity alone does not trigger Level 2. A case with multiple live burdens and a plain `/daee-epistemics` invocation still runs at Level 1. The full recursive traversal runs internally; only the visible machinery differs.

**Full recursion still required at Level 1:**
Recursive-audit discipline runs in every mode. Level determines how much diagnostic machinery is printed, not whether recursion occurs.
The same-response RECURSE trigger checklist still governs Level 1 internally: if the current blocker cleared, another already-present burden remains live, and no stop/hold/gate/limit blocks it, the answer must continue through the next bounded prose move rather than rendering prose closure.

```text
claim being assessed
→ upstream criterion / tribunal / hidden premise
→ first-order content
→ higher-order burden
→ downstream entailments
→ adjacent already-present distortions
→ state re-read
→ STOP / HOLD / RECURSE / PARTIAL
```

This traversal must be visible through the mandatory compact DSL/IR header plus state-transition progression, not printed gate machinery. The response progresses through live burdens before final synthesis:

```text
bounded move
→ state re-read: what cleared
→ what remains live
→ next eligible burden
→ decision
→ next bounded move when internally licensed, or prose partial status when limits block it
```

If same-response recursion is internally licensed in Level 1, visible progression must include a short
prose state transition: what the prior move cleared, what remains live, why that live
burden was already present in the original input, and why the next bounded move is now
eligible. Bare essay headings such as "Move 1", "Move 2", or "Move 3" do not satisfy
RECURSE. They are section ordering unless the refreshed-state relation is stated.

TTP activation must also be operational, not merely named. Saying "the M1 move" or
"the M8 move" does not prove the TTP ran. The output must reflect the bounded operation
selected by the validated case-state / IR while avoiding a `matched_modules` ledger in
default mode.
Visible `Operation:` lines must begin with a closed operative verb from the existing
operator grammar: `split`, `distinguish`, `test against own grounds`, `disambiguate`,
`classify`, `audit`, `reclassify`, `narrow`, `expose`, `re-read`, `sequence`,
`refuse jurisdiction of`, or `clear`. Generic verbs such as `address`, `discuss`,
`explore`, `engage`, or `consider` are non-operative operation verbs.

Minimum substantive operation requirement: each rendered operation must apply the
owner-specific operation floor, not merely show the words Target/Operation/Result. The
operation must pressure a live premise, predicate, criterion, warrant, or branch; the result
must change burden-state; and the state/noetic re-read must show the cumulative-state delta.
If the section shape is present but the claim-state does not narrow, collapse, clear, hold,
or become partial, the output is rubric-schematic and must be rewritten before emission.

**Minimum visible transition spine (mandatory in multi-burden default):**
A live burden is an input-anchored noetic-state burden, not merely a topic mentioned in the
prompt. topic transition != recursion; component tour != recursion. State re-read enumeration
of remaining input-anchored live burdens + one newly routed bounded pass = recursion.

In any multi-burden case the response must include a minimum visible transition spine. The
minimum permitted form is:
"That clears [X]. The remaining live issue already present in the input is [Y]. The next
bounded step is [Z]."

The transition spine must mark case-state re-read, not topical movement. Each transition must
show what the prior operator cleared, what input-anchored live burden state re-read identified
as remaining, and what the next bounded step is. If no transition marker appears when state
re-read identifies a remaining input-anchored live burden and licenses a newly routed bounded
pass, the output is clean essay cosplay and must be rewritten before emission. A multi-burden
default answer without transition spine is invalid even if it is clean, accurate, and
well-written. Minimum visible transition spine is required for multi-burden default output.
Topic-organized output without state re-read transitions fails governed traversal.

When state re-read names a remaining input-anchored burden and no named gate blocks it,
Restorative Response and Closing Formulation are not yet licensed. Continue with the next
bounded burden-cycle. If response limits prevent that continuation, mark PARTIAL with the
next live burden instead of closing rhetorically.

For this gate, "input-anchored" includes supporting premises and contrast rules already
present in the user's surface discourse, not only separate requested questions. A public/private
partition, source-status rule, translation demand, or moral/epistemic criterion named in the
input remains eligible for recheck after the upstream blocker lands.
If the state re-read enumerates such remaining burdens, the render may not say "only if
requested" and then close unless it also names the hold gate blocking release. "This needs its
own bounded pass" means continue with that pass or mark PARTIAL.

**Final closure in multi-burden default (mandatory):**
In multi-burden default responses, final closure must include a brief prose confirmation that
no further same-input eligible burden remains, or must mark HOLD/PARTIAL with reason.
Allowed: "At this point the live burdens in the original statement have been handled at the
level needed for this response."
Forbidden: literal governance labels such as "Recursion decision: STOP".

**Required compact DSL/IR header for default (minimum visible form):**

Each default burden-cycle must follow this structure. Layer B is prose-first; Layer A and
state/noetic re-read use compact entries. Default Layer A is fit-for-purpose but mandatory:
it prints only the compact DSL/IR header needed to make the current pass governable. This
Layer A block is the compact diagnostic frame for default mode; it is not raw Diagnostic IR.
The full-field compact header is a deliberate anti-cosplay tradeoff: simple cases still show the
minimum compiler trace needed to prove governed execution without exposing raw IR.

```text
## Burden-Cycle N
### Layer A — Compact DSL/IR header
- read status: [dominant | distributed | underdetermined]
- confidence: [strong | provisional | low]
- claim_level: [first-order | meta-epistemic | meta-ontological | meta-noetic | cross-level]
- pattern_profile: [PF overlay or none]
- reason-category: [1 | 2 | 3 | 4]
- concealment: [clear | mode-? | compact anchored mode]
- deformation: [primary/secondary deformation read or none/underdetermined]
- DO-orient: [truth-seek | identity-perf | autotelic | zann-mode | mixed]
- live noetic burden: [input-anchored noetic-state burden governing this pass]
- current bounded operator: [what the operator does, by function — not a module label]
- held: [what remains held and why, or none]
- source-status/noetic-frame: [selected operative frame and any non-operative status]
- decisive missing differentiator: [only when required]
- gate/release decision: [compact release status; no raw `Recursion decision:` label]

### Layer B — bounded governed response

#### Hidden Premises
[Compactly name the hidden premise(s), imported criterion, concealment/deformation, or warrant disorder that governs the released operation.]

#### Burden / Operation 1
##### Core Formulation
[Local operative compression: governing deformation/concealment/deviation; the noetic/modal pattern by which it functions; and the restoration vector by which sound order is recovered.]

##### Bounded Response / operative submoves
[Execute only the selected bounded operator and justified submoves for this released burden. Not a general essay. No meta narration.]

#### TTP/operator trace
[Required when a named operator performs runtime work. Name the operator and keep target -> operation -> result visible. This is not external citation support and not a `matched_modules` dump, bibliography parade, scholar/source parade, school-label context, genealogy, external theorist support, or public-render prestige support.]

### State/noetic re-read
- Cleared:                      [what this live burden cleared]
- Remaining input-anchored burdens: [enumerated from original input, not a topic list]
- Held routes rechecked:        [result after this pass]
- Next bounded pass:            [prose reason if another bounded pass is licensed]
- Release status:               [prose closure/hold/partial/continuation status; no literal STOP/HOLD/RECURSE/PARTIAL label]

### Restorative Response
[Required once in default output after the final state/noetic re-read. Bounded to what the released operation(s) actually landed. Do not promote it into a new burden-cycle. Do not release held downstream burdens. If state/noetic re-read licenses another same-input burden, continue first.]

### Closing Formulation
[Required once at the very end after Restorative Response. Synthesize what cleared, what remains held, and the final governed takeaway. Do not substitute for state/noetic re-read.]
```

If the release status says another bounded pass is licensed, continue with Burden-Cycle N+1.
If closure, hold, or partial traversal is correct, state the reason in prose — no literal
STOP / HOLD / RECURSE / PARTIAL governance label in default mode.

**Layer A required default fields:** read status, confidence, claim_level,
pattern_profile, reason-category, concealment, deformation, DO-orient, live noetic
burden, current bounded operator (by function), held, source-status/noetic-frame, and
gate/release decision. `Decisive missing differentiator` is conditional:
include it when confidence is not `strong` or read status is not `dominant`, or when the
case is otherwise thin, mixed, distributed, or underdetermined. These fields are render-time
aliases of existing diagnostic state; they add no IR fields, routes, PF codes, or owners.
Do not omit the compact DSL/IR header in default mode.

Current bounded operator is one live noetic burden/function: `B`, not a route chain,
module list, route itinerary, single operative submove, or lone `s`. Allowed examples: `imported moral tribunal /
worship-worthiness criterion burden`, `foundational epistemology warrant burden`, or
`source-status / identity-stabilization burden`. Forbidden examples: `FPD -> M1 -> DO-8 ->
M8 -> restoration`, `M1, M8, DO-8, restoration`, `full route itinerary`, or splitting imported
criterion, hujjah/accountability, and hiddenness-frame correction into separate pass-level
operators when they serve the same tribunal burden. A route chain is not a bounded operator.

**Submove-vs-recursion rule:** use `recursive-state-transitions.md` notation:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
Gloss: Operative submoves do not become burden-cycles; `hujjah/accountability correction`,
`guidance-as-coercive-proof correction`, hiddenness, punishment/accountability, source-status,
source-worldview, and identity-stabilization may be `s` inside one governing `B` when needed
to land it. They become separate burden-cycles only after the current gated operation lands and
the state/noetic re-read shows a genuinely new input-anchored live burden. Multi-burden does
not mean multi-recursion by default.

**TTP entry / exit visibility:** Default mode does not need to print an audit ledger, but the
answer must be visibly compatible with TTP entry and exit criteria. The current live burden
must have a bounded target; each operative submove must perform an operation and produce a
result; those results must feed a burden landing; and the next live burden transition must come from
state re-read. A response that names a TTP, then moves to a downstream topic without burden landing
and refresh, is invalid even if it is accurate.

Hard default output may expose `Operative Submove` or `B<N>.s<i>` labels under one burden.
This is not a raw IR, route ledger, or load ledger when each submove is case-specific and
feeds `Land(B)` before `R(H,Δ)`. A complex `B` rendered as one generic
Target/Operation/Result block while necessary submoves remain implicit is hard-output
compression failure; a single block is sufficient only for a genuinely atomic burden.

Hard-output render-through template:

```text
Burden N: <name>
  Operative Submove B<N>.s1:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <closed operative verb>
    Result: <changed claim-state>
  Operative Submove B<N>.s2:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <closed operative verb>
    Result: <changed claim-state>
  [continue until all materially necessary s are rendered]
  Land(B<N>): <cumulative state delta from s1...sn>
  R(H,Δ): <held/released/next-live-burden decision>
```

This template is the visible hard-output form for `ComplexB`; it is not a full procedural
audit, raw IR dump, or route ledger when the fields are case-specific and serve the same
live burden. `AtomicB` may render one submove only when the burden has one target, one
operation, and no distinct internal predicates, criteria, source-status forks, or release gates.
For hard smoke or hard default execution, visible submoves must be backed by owner-body access:
root summary recognition, module-label memory, or `matched_modules` naming is not enough.
Before rendering a complex `B.s<i>`, the active TTP owner body or compiled bundle section
containing its operation floor must be loaded/read, unless that exact section is already present
in active context. Package availability, map presence, or bundle co-location is not access, and
trace/verdict evidence must not overclaim beyond that access. If the owner body or compiled bundle section cannot be
loaded or identified, the hard output must mark `PARTIAL / OWNER-BODY-NOT-LOADED` with
the missing owner/path rather than rendering a generic Target/Operation/Result block. This marker
is a required hard-output failure marker and is permitted in default/hard output.

**Layer B governed-response shape (mandatory):** Default Layer B must visibly contain Hidden
Premises and one Core Formulation for each released live noetic burden / governed operation.
Core Formulation is local to the released operation: it is a compact operative formulation
identifying how sound/innate reason has been deformed, concealed, or deviated from; the
modality/pattern by which the unsoundness operates; and the restoration vector by which the
noetic structure is resolved or returned toward sound order. It is not a summary, conclusion,
bibliography, or rhetorical flourish. The bounded response / operative submoves execute that Core Formulation.
Missing Core Formulation or essay-only Layer B is a render failure.

Restorative Response is required once in default output after the final state/noetic re-read. It is bounded
to what the current operation(s) actually landed; it is not optional, not pastoral expansion, not
a new burden-cycle by default, and not a license to release held downstream burdens. It identifies
what order is restored, what criterion/source/warrant is returned to its proper place, what
deformation or concealment is relieved, and what remains held if not yet restorable.

Closing Formulation is required once at the very end, after Restorative Response. It synthesizes
what was cleared, what remains held, and the final governed takeaway. Do not require Closing
Formulation inside each burden. Do not let Closing Formulation substitute for state/noetic re-read.
Do not make every burden self-close rhetorically. Closing before state/noetic re-read is a render
failure.

Non-trivial operators require a compact TTP/operator trace when that trace helps audit execution;
this is not a `matched_modules` dump and does not authorize public source, scholar, school,
genealogy, bibliography, or external-theorist support.

**TTP/operator invocation trace:** Do not confuse source-citation discipline with
TTP/operator trace discipline. Default output avoids scholar/source/citation parade, but when
a TTP/operator actually performs the work it must be explicitly identified in the governed
operation or bounded response. This includes reductio, tamanu, criterion-reversal,
tribunal-detection, predication repair, authority-order repair, and any other named operator.
No invisible TTP execution; no generic prose replacing named operator use; no argument-bank dump
under an unnamed TTP; no TTP name used decoratively without target -> operation -> result; no
source citation substituted for TTP invocation; and no TTP invocation substituted for
Qur'an/Sunnah/Salaf citation when revealed textual support is actually used.

**Burden-complete operator routing:** within the released live burden, matched
TTPs/operators must address materially necessary sub-burdens before `R`. Do not answer only
the headline objection, skip internal sub-burdens, substitute generic prose for routed
execution, or jump straight to a broad conclusion. `R` may expose a deeper governing
epistemology as `NewB`, first-order repairs, held higher-order rebuttals, or STOP/HOLD/
PARTIAL/RECURSE, but `NewB` is not licensed until the current burden and its necessary
sub-burdens have actually been operated on.

**Bounded release cap:** Layer B may release at most three major operative submoves inside one
governing burden unless state/noetic re-read licenses a new burden-cycle. More than three major
moves in one Layer B is an argument dump unless held/PARTIAL/RECURSE handling makes the boundary
explicit. A fourth major submove also requires the submove saturation gate: the next submove
must share the same target-family, claim-level, source/noetic frame, claim cluster, and
restoration vector, and must be materially necessary to land the current burden. Otherwise
the current burden must land and state must be re-read before more material is released.

**Rubric-skeleton failure:** A default answer fails even when every heading is present if it:
- asserts "this burden lands" without owner-specific operation and cumulative-state delta;
- repeats the rubric vocabulary while giving generic prose instead of operative pressure;
- treats TTP names as decorative labels rather than operations;
- makes a state/noetic re-read that only restates cleared/held/decision without saying what changed;
- starts a new burden-cycle without passing the NewB license test;
- builds size by repeating runtime-proof or compliance language rather than executing the burden.

**Scaffold-language failure:** Default output fails if it explains the smoke/test harness,
owner-floor compliance, or runtime proof instead of answering the case. Forbidden default
phrases include "this smoke artifact", "runtime constraint being tested", "owner floor is
applied", "owner-floor pressure", "the TTP has to change something",
"burden-completeness check", "the operation is bounded to the target named above", or any
generic paragraph about target / operation / result whose function is to prove compliance
rather than perform the operation. Those belong in trace/verdict artifacts only.
Likewise, repeated formula paragraphs such as "That test changes the force of the case",
"The result is a real state change", or other reusable test/result boilerplate fail default
render even if the surrounding nouns are case-specific. Operation prose must be live
case-pressure, not a fill-in compliance frame.
Reusable hinge/load-bearing boilerplate also fails default render. Phrases such as
"load-bearing point", "if that point is left vague", "this exact pressure can stand",
"surrounding topic is held back", "the live hinge can be tested", "case-state after
this pressure", or "the move forces the inference to carry its own burden" describe
proof-of-execution, not the case itself. They belong, if at all, in `trace.md` or
`verdict.md`, never in user-facing default output.

**Fixture/case contamination failure:** Default output must not import case-specific
language from another fixture, example, or smoke family. Named source-worldview
hard-smoke frames, quoted hard-smoke phrases, accountability/punishment/hell
language, source-status biography language, or moral-protest/hiddenness language
may appear only when the current input and validated IR release that burden-family.
Cross-fixture prose reuse is a render failure even when headings and operator trace
are present.

**Artifact separation:** default output is the user-facing runtime result. It is not the trace
file and not the verdict file. Runtime proof, loaded-file proof, checker proof, smoke execution
metadata, and fixture audit text belong in trace/verdict artifacts or internal/development audit,
not in default Layer A or Layer B.

**Layer A / Layer B release check:** Layer A is diagnostic control, not an answer bank. Layer B
is the permitted bounded response, not a place to unload all held material named in Layer A.
If Layer A lists a held route and Layer B answers it before state re-read licenses it, the render
has become Layer A/B smuggling. Rewrite as one bounded live burden, then refresh.
Held-route semantic leakage is the stricter form of this failure: a noun phrase listed
in `held` or `Held routes` cannot appear in Layer B as an answered topical commitment
unless a preceding state/noetic re-read explicitly released it with `Released: <item>`,
`Released routes: <item>`, or `Newly released routes: <item>`.

**Layer A must not show:** full Diagnostic IR, full Case State, source_basis,
matched_modules, load ledger, route itinerary (e.g., Next: FPD → M1 → M8), NS codes in
field-printout form (unless the NS code is the governing issue), or broad concealment /
deformation verdict dumps without anchoring signal. The compact lowercase `concealment:`
and `deformation:` fields above are permitted only as bounded DSL/IR anchors, not as
expanded interior-certification ledgers.

**Default compact DSL/IR header:** The Layer A block above is the compact visible
diagnostic compiler trace. It is the default compact diagnostic frame, not the full
internal/audit diagnostic record. The default header restricts visible fields to the
required field set; everything else remains internal. It must surface enough governing
diagnostic fact for the current pass to be auditable as compiler traversal rather than essay.

**Compact state re-read:** The state re-read block above is compact. It must enumerate
remaining input-anchored burdens, not merely state a governance decision. A line such as
"Governance: STOP" is forbidden in default output and is not a valid state re-read. The
default must show that no input-anchored eligible burden remains, or name the burden and
the prose reason for a hold or partial close.

**Single-Pass Layer A/B Cosplay:** A response that prints Layer A + Layer B + state re-read
exactly once and then stops — without proving no eligible input-anchored live burden remains,
or without continuing when state re-read licenses another bounded pass. This is a recursion failure, not a
structured response. The burden-cycle shape is not satisfied by printing it once. It must be
repeated for each eligible input-anchored live burden until governed recursive sufficiency.

**Internal requirements still apply even when not visible:**
- Case-state resolved internally.
- Governing burden identified internally.
- Upstream blocker cleared or named.
- Downstream held if unresolved.
- Output-release rubric passed.
- STOP / HOLD / RECURSE / PARTIAL decision made.
- Post-render gate run before ending.
- Default compact DSL/IR header, Hidden Premises, per-operation Core Formulation,
  bounded operation, state/noetic re-read, one Restorative Response, and one final
  Closing Formulation rendered; literal final-governance
  fields remain internal unless `:dsl`, internal/development audit, pass-review, or diagnostic
  trace was requested.

**Default Final-Output Preflight Gate (mandatory):**
Before emitting any Level 1 / default `/daee-epistemics` answer, scan the proposed final
response. This is a final-output gate, not a render preference. If the proposed response
contains any prohibited scaffolding, route plan, or meta-composition prefix, the response is
invalid and must be rewritten before output as clean governed prose.

The Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It also
checks pipeline validity: internal diagnosis -> validated IR -> routed operator selection
-> output-release rubric -> diagnostic-render-contract -> state re-read -> post-render
gate -> STOP / HOLD / RECURSE / PARTIAL decision. Output-release decides what may be
released; diagnostic-render-contract decides how it appears; the preflight gate enforces both
at the last mile. If the answer is clean prose but was produced by topical essay
sequencing, it is invalid and must be rewritten.

Use `recursive-state-transitions.md` for the canonical default transition skeleton and
no-premature-STOP recursion rules.

Pipeline-validity check for Level 1:
- V1 / diagnosis ran before answer.
- Phase 2 passes ran where triggered.
- Diagnostic IR formed internally before routing.
- Routing came from validated IR.
- TTP selected as operator, not prose label.
- Output-release rubric applied before visible render.
- Render contract applied before final prose.
- state re-readed after the bounded move.
- Post-render gate run before closure.
- STOP / HOLD / RECURSE / PARTIAL decision made before ending.

Preflight recursion check: after the first bounded move, ask what cleared, what remains
live, whether the remaining live burden was already present in the original input, whether it is
now eligible, and whether any stop/register/semantic/thin-basis gate blocks it. If another
eligible same-input live burden remains after the current blocker clears, default output must
continue with one bounded next pass using a prose state transition, or render partial
release-status prose if limits prevent doing so. It may not silently close.

Preflight NewB check: a next burden-cycle is valid only if the prior burden landed through
owner-specific operation, cumulative-state delta is visible, the proposed next burden was
already input-anchored or held, the proposed next burden differs materially from the prior
burden by live target/function/restoration vector, and no gate blocks release. Otherwise the
material remains a submove, HOLD, or PARTIAL.

For the canonical valid default-mode transition example and invalid Step/Move contrast,
use `recursive-state-transitions.md`.

TTP labels do not satisfy execution. TTPs are surgical interventions, not essay sections.
A default answer may briefly name an operation/module
label if helpful, but the operation must be visible: bounded target, operation performed,
result of the operation, and state re-read before any next operator.

Layer A contrast pairs:
- Permitted default prose: "The objection imports a moral tribunal that has not justified its
  authority."
- Permitted default compact Layer A fields: `- claim_level:`, `- reason-category:`,
  `- live noetic burden: imported moral criterion`, and `- gate/release decision:`.
- Banned default field printouts: `Foreign premise: detected`, `Concealment: irad primary`,
  `Deformation: hawa primary`, `NS-4/NS-5`, and `Recursion decision: RECURSE`.

Rule: prose diagnostic fact is allowed; field-style printout is not default output.
"Field-style printout" in this rule refers to the full IR / Case-State field set and verdict
dumps — not the compact Layer A DSL/IR header. The compact Layer A header is the explicitly
permitted exception: it may show read status, confidence, claim_level, pattern_profile,
reason-category, concealment, deformation, DO-orient, live noetic burden, current bounded
operator, held, source-status/noetic-frame, decisive missing differentiator when required,
and gate/release decision. Layer A must not show the forbidden set above.

Default final-output failure tokens include:
- "Now I have enough", "I now have enough", or "I now have sufficient".
- "Let me compose", "Let me write", "Let me craft", or
  "Let me construct the diagnostic IR".
- "Let me check", "Let me also quickly check", or "I will produce governed prose".
- `## Diagnostic IR`, `[Diagnostic IR]`, `Case State:`, a full IR/case-state field block,
  `matched_modules`, `source_basis`, load ledger, route ledger, planned route list, or
  a visible route plan such as `Next: FPD -> ...`.
- Strong interior-classification verdict dumps such as `Concealment: irad primary`,
  `Deformation: hawa primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. The compact lowercase Layer A fields are
  allowed only as bounded DSL/IR anchors.
- A bibliography, "Primary Sources Referenced", external research-style source list, or
  source-basis ledger in default mode unless sources/citations were requested.
- Bare "Step 1 / Step 2 / Step 3 / Step 4" or "Move 1 / Move 2 / Move 3" sequencing
  when offered as recursion.
- `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`, or any variant where a
  route itinerary is printed as the bounded operator.
- "Smoke runtime note", "Runtime grounding detail", "Skill invocation proof",
  "loaded before output", "proof of loaded files", or other audit/proof boilerplate in
  default output. Output artifact is not trace artifact; output.md != trace.md != verdict.md.
- "Pass 1 / Pass 2 / Pass 3" headings for FPD, M1, DO-8, M8, identity clarification, or
  restoration fragments that are merely operative submoves under one burden.
- "Pass 1 / Pass 2 / Pass 3" headings for imported criterion, hujjah/accountability, and
  guidance-as-coercive-proof corrections when those operations are all clearing the same
  imported moral tribunal / worship-worthiness criterion burden.
- Restoration synthesis or pastoral note before the active burden landing and state re-read.

Rewrite-before-output rule: replace the failed surface with compact prose that names only
the governing diagnostic fact needed for the answer. A valid default opening may say: "This
objection has three layers: an imported moral criterion, a hiddenness claim, and a
punishment/accountability claim. The criterion has to be tested first, because otherwise
the answer would let the objection judge revelation by a standard it has not justified."
Then continue with bounded prose. Do not print the IR, case state, matched route, or route
plan.

**Must not:**
- Print meta-composition prefixes or close variants such as "Now I have enough...",
  "Now I have enough to compose...", "I now have enough...",
  "I now have sufficient...", "I now have sufficient grounding...",
  "Let me compose...", "Let me write...", "Let me write it...",
  "Let me craft...", or "I'll now compose...".
- Print "Let me construct the diagnostic IR" or equivalent narration of internal setup.
- Pretend diagnosis was unnecessary.
- Release downstream content before upstream blockers clear.
- Hide held material when the user needs to know why the answer is bounded.
- Treat state re-read as only waiting for a user response.
- Close with STOP before the post-render gate has rechecked held material.
- Stop after the first good move when the original input contains another eligible live burden.
- Print the `[Diagnostic IR]` code-fenced block or any `## Diagnostic IR` section header.
- Print any header equivalent to `## Diagnostic IR (Internal - Governing the Response)`.
- Print `Case State:` or a full `[Case State]` block with all IR fields populated.
- Print `matched_modules` or route-owner ledger lines.
- Print `source_basis`, route ledger, planned route list, or a visible route plan such as
  `Next: FPD -> ...`.
- Print strong interior-classification verdict dumps such as `Concealment: irad primary`,
  `Deformation: hawa primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. In default prose, prefer:
  "The public identity-frame may stabilize the objection's moral criterion, but that is not
  a claim to know the person's inner motive."
- Print a Load Ledger or bundle resolution table.
- Print a Render Permission Check or source-basis printout.
- Print a bibliography, "Primary Sources Referenced", external research-style source
  list, or source-basis ledger unless the user explicitly requested citations/sources
  or the task is internal/development audit or research.
- Print the full procedural audit template or any code-fenced IR listing. The compact
  hard-output render-through template above is allowed when it renders case-specific
  submoves under the same live burden.
- Print smoke/runtime proof boilerplate, loaded-file proof, checker proof, or verdict
  material inside default output.
- Apply Level 2 or Level 3 render shape solely because the case has multiple live burdens.

---

### Level 2 — Compact Diagnostic / Lab-Report Response

**Use when (invocation gating required — secondary conditions alone do not trigger Level 2):**
- The user invokes `/daee-epistemics:dsl`. **This is the gating condition.**
- OR the user explicitly asks for compact diagnostic output, DSL render, or lab-report format.

Plain `/daee-epistemics` never triggers Level 2, regardless of case complexity, number of live burdens, or whether diagnostic transparency would be useful. If the invocation is plain, Level 1 applies. Full recursion still runs; only the visible machinery differs.

Secondary conditions (apply only when the gating condition above is met):
- The case has multiple live burdens.
- Diagnostic transparency materially helps.
- The answer must show what is governing first.
- Downstream material is held.
- Recursive traversal needs to be visible.
- The response needs to distinguish anchored, inferred, and speculative material.
- The user is testing whether the skill routed correctly.

**Recommended visible shape:**

```md
## Compact DSL / IR
- Read status:
- Confidence:
- Live noetic burden:
- Current bounded operator:
- Held:
- Decisive missing differentiator:
- Selected IR fields:

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
- Do not expose PF codes or matched module names unless they help the user trace a compact IR decision.
- Do not let the diagnostic section become a broad procedural audit.
- Do not release downstream content merely because it is named in a section header.
- Do not treat compact diagnostic render as permission to dump all internal machinery.
- Do not include the full verbose load ledger; that belongs only to internal/development audit when useful.
- Do not treat the Post-Render Gate section as merely waiting for user response. State whether same-response recursion is required, blocked, partial, or complete and why.
- If recursive traversal is visible, use one live burden per burden-cycle: Live noetic burden, Why already present, Released module(s), Bounded move, state re-read, and Governance. Recursion is not argument dump.

---

### Level 3 — Internal/Development Audit Render

**Use only when:**
- The task is internal/development audit, regression review, or procedural debugging.
- The user invokes `/daee-epistemics:audit` in that internal/development context.
- The user asks for pass-review.
- The user asks for regression testing.
- The user asks for source-basis trace.
- The user asks whether the skill routed correctly.
- The task is a patch report or architecture test rather than answering an ordinary interlocutor.

`/daee-epistemics:audit` is not a public-facing render mode for ordinary interlocutor
answers. If invoked for ordinary response work, treat it as deprecated and prefer `:dsl`
for concise visible diagnostic structure or default mode for governed response.

**Full shape:**

```md
# Output — <Burden-Cycle Number or "Initial daee-epistemics Response">

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

**When to surface matched module names / IDs:** Only in internal/development audit, or in Level 2 when the user needs to trace which module governed a routing decision. Do not turn this into a route ledger.

**When to surface backbone predicates:** Only when a backbone predicate emission (C, T, O, or K group) materially changed the routing gate or suppression rule in this pass.

**When to suppress raw internal fields:** Level 1 default response suppresses raw diagnostic machinery, but it must still print the compact DSL/IR header and state/noetic re-read. Literal labels such as `Recursion decision:`, `next_eligible_pass:`, `post_render_gate:`, and visible STOP / HOLD / RECURSE / PARTIAL governance fields belong to `:dsl`, internal/development audit, pass-review, or diagnostic trace.

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

`[Restoration Trace]` appears in internal/development audit render and may appear in Level 2 when the trace materially explains why only this much was released. It must record:

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

In an internal/development audit render, the `[Restorative Response]` must mark held Layer B deployment explicitly: "Layer B: held — [reason]." The content does not appear.

---

## Post-Render Gate / Final Governance Section

This section is mandatory in the governing state after every bounded restorative move. Level 2 and
internal/development audit may surface the full gate when recursion, state re-read, or the
continuation decision materially governs the visible answer. Level 1 does not print the raw gate
or literal field labels; it prints `State/noetic re-read` plus compact content. When the
continuation decision materially governs a default answer, render it as a state transition:
what cleared, what remains live, why that burden was already present, why it is now eligible, and
the one bounded next pass.

Internally, and visibly in `:dsl`, internal/development audit, pass-review, or diagnostic trace, it must answer:
- **Cleared this pass:** What did the bounded move actually clear?
- **Remaining live distortions:** What pressure remains live in the same input?
- **Held routes rechecked:** Which held routes were tested after refresh?
- **Newly released routes:** Did any held route become newly eligible?
- **Next eligible pass:** What is the next bounded pass, or is there none?
- **Recursion decision:** STOP, HOLD, RECURSE, or PARTIAL.

Decision rules:
- **STOP** is valid only if no live distortion remains, no eligible live burden remains, and no held route has become eligible.
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
5. **Level 3 as default:** Level 3 internal/development audit render is not the default format. It applies only for regression, pass-review, source-basis trace, architecture testing, or procedural debugging.
6. **Codex patch-report format as runtime output:** Patch-report structure (files inspected, implementation verdict, changelog) is not a runtime response format.
7. **Suppressing Level 2 when diagnostic transparency is needed:** If the user invoked `/daee-epistemics:dsl` or explicitly asked for compact diagnostic output, withholding Level 2 structure without a clear reason harms routing legibility.
8. **Hiding refreshed-state decision:** If a governing blocker was cleared in this pass and a downstream burden remains live, the response must show the refreshed-state decision — not silently hold the downstream material as though the blocker had not cleared.
9. **Premature closure without re-entry:** Do not render one strong move and close without running the post-render gate, rechecking held routes, and internally deciding STOP, HOLD, RECURSE, or PARTIAL.
10. **Printing the IR schema as the response:** Do not print the `[Diagnostic IR]` code-fenced block or a `## Diagnostic IR` section header in the public response in default mode. The Full IR Schema in `diagnostic-ir.md` is the internal state object for the dispatch gate - not a printout template. Discipline is universal; printout is mode-specific. Recursive-audit discipline applies in every mode; the full audit printout belongs only to internal/development audit. In default mode, literal governance labels such as `Recursion decision:` and `next_eligible_pass:` are prohibited; use the compact DSL/IR header and state/noetic re-read instead.
11. **Meta-composition leakage:** Do not show private drafting phrases such as "Now I have enough...", "Now I have enough to compose...", "I now have enough...", "I now have sufficient...", "I now have sufficient grounding...", "Let me compose...", "Let me write...", "Let me write it...", "Let me craft...", or "I'll now compose..." in any runtime answer. Those are composition notes, not skill output.
12. **Stacking without transition:** If same-response recursion is required, the answer must include a prose state-change transition: what landed, what changed, and why the next bounded move is now eligible. Simply placing another module section after the first is not governed recursion.
13. **Essay headings as fake recursion:** "Move 1 / Move 2 / Move 3" headings do not satisfy RECURSE unless the response shows state re-read between passes and explains why the next already-present burden is eligible.
14. **Default source-list dump:** In Level 1, do not end with a bibliography, "Primary Sources Referenced", source-basis ledger, or external research-style source list unless the user requested sources or the task is internal/development audit or research. Short form: no source/bibliography dump in default mode unless requested. Integrate essential references compactly in prose instead.
15. **Route Cosplay Failure:** Do not print route machinery as proof of compliance. In default mode, Diagnostic IR, Case State, `matched_modules`, literal `Recursion decision:`, and TTP labels do not substitute for target -> operation -> result -> state re-read.
16. **One-time TTP itinerary:** Do not apply TTPs only once against the initial case-state and then answer every detected topic. TTPs execute across refreshed case-states: after each bounded operator lands, the refreshed state determines whether an already-present same-input burden is eligible, held, partial, or closed. Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future contingencies stay held with a release condition.
17. **Premature compression:** Do not shorten default output by skipping an eligible same-input burden. The failure is essay sprawl without refresh, not governed recursive sufficiency.
18. **Wrong optimization target:** Do not optimize for short output or long output. Optimize the render for governed recursive sufficiency: compact DSL/IR header plus bounded prose in default mode, compact pass trace in `:dsl`, full ledger only in internal/development audit.
19. **Clean Essay Cosplay:** Every pass must show a transition before the next bounded operator starts. Multiple topical sections without state re-read transitions, hidden premises listed without operator result, doctrine dumped after criterion correction, or a pastoral close added without final state re-read are default-mode failures.
20. **Identity over-certification:** In default mode, "the public identity-frame may stabilize the criterion or affect discourse orientation" is permitted when grounded. Unsafe default verdicts include "the identity layer is heavily load-bearing," "his identity is the framework through which every claim is processed," "it is hawa," or "it is irad," unless independently grounded and source-status marked.
21. **Route-chain bounded operator:** Do not render `Current bounded operator` as `FPD -> M1 -> DO-8 -> M8 -> restoration`, `M1, M8, DO-8, restoration`, or any module itinerary. The field names one burden-level function selected after diagnostic reduction and routing precedence.
22. **Route-chain recursion cosplay:** Do not turn route legs into `Pass 1`, `Pass 2`, and `Pass 3`. Those are operative submoves unless a prior burden landed, state re-read ran, and the next input-anchored burden was licensed.
23. **Restoration before state re-read:** Do not append restoration synthesis or pastoral note before the active burden has landed and state re-read licenses closure, HOLD, PARTIAL, or the next live burden.
24. **Noetic-frame equivalence stack:** Use the canonical notation in `references/diagnostics/recursive-state-transitions.md`: `N_AT` aliases count once; `N_Ashʿarī[*]` and `N_Māturīdī[*]` are family labels, not automatic operative `N`; `family label != operative N`; `shared vocabulary != shared warrant`; `σ_context != σ_warrant`. Do not flatten rival frames under umbrella terms (`classical theology`, `the classical tradition`, `mainstream kalam`, `Ashari/Maturidi tradition`) when the claim is school-sensitive or disputed.
25. **Contrast-source-as-operative-support:** Do not name a source as `contrast`, `opponent-position`, `historical note`, `genealogy`, `held material`, or `bounded comparison` and then use the same source as operative warrant in the same burden-cycle without explicit reclassification.
26. **Ungrounded noetic re-read:** Do not render a `state re-read` / `noetic re-read` whose `burden landed` is asserted without an immediately preceding operative submove with `target -> operation -> result`, or whose `still live` / `next licensed live burden` is not anchored in the original input, prior held material, or the preceding collapse radius. Field-grounding rules are in `references/diagnostics/recursive-state-transitions.md §Grounded Noetic Re-Read Shape`.
27. **Method-source branding:** Do not publicly frame daee-epistemics as a named-school methodology, new creed, new aqidah, new noetics, named-scholar method, or authority-by-association project. Default/public framing is sound noetic diagnosis -> detection of deformation/concealment/criterion import -> restoration of proper warrant/order and proper cognitive function in a congenial epistemic milieu.
28. **Default source/citation restriction:** In default output, school, author, citation, genealogy, external philosopher, theologian, or framework references are not public-render material unless the user explicitly asks for them or validated IR specifically requires source-comparison. Default citation allowance is restricted to Qur'an, Sunnah, and sound narrations from the Salaf, and any such use must be directly referenced through an external source.

---

## Grounded Noetic Re-Read Render Shape

For default-mode prose, the canonical state re-read transition is:
"That landed [X]. What remains live is [Y]. What is held is [Z]. The next licensed live
burden is [W]." — where each clause is grounded as defined in
`references/diagnostics/recursive-state-transitions.md §Grounded Noetic Re-Read Shape`.

For `:dsl` / internal-development audit / pass-review / diagnostic-trace, the compact field block is:

```text
Noetic re-read:
- burden landed:
- still live:
- held:
- recursion decision:
- next licensed live burden:
```

Field-grounding rules apply in every mode. Printing the field block does not satisfy
the grounding rules. The compact state re-read fields used in the default Layer B
burden-cycle shape (`Cleared`, `Remaining input-anchored burdens`, `Held routes
rechecked`, `Next bounded pass`, `Governance`) are equivalent surface forms; they map to
the same grounded shape and are subject to the same grounding rules.

**Source-status discipline in render:** use `recursive-state-transitions.md` notation:
`N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī`; `N_Ashʿarī[*]` and
`N_Māturīdī[*]` are family labels, not automatic operative `N`; `σ_context != σ_warrant`.
Gloss: each burden-cycle renders one operative noetic frame; `N_AT` aliases are not multiple
warrants, family labels are not operative support, and contradictory frames may appear only
under non-operative source-status. Render shapes such as "the classical tradition agrees"
or "Islamic tradition says" are forbidden in default mode when school-sensitive or disputed.
Default output normally does not render non-operative `σ` sources at all. School, author,
genealogy, external philosopher/theologian, framework, or contextual-source references are held
unless explicitly requested by the user or required by validated source-comparison IR. When an
internal/development, `:dsl`, pass-review, or IR-required source-comparison render names
non-operative `σ`, include the `Operative warrant:` sentence and the specific non-premise clause:
the non-operative source does not contribute to the warrant; specifically, the named
contrast/opponent/history/genealogy/held/comparison element is not used as a premise here.

---

## Default-Mode Worked Example

**Input.** "If God really has eternal knowledge, power, and will, doesn't that make God
composed of distinct attributes? And if composed, then dependent on parts, like everything
else?"

### Layer A — Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-ontological
- pattern_profile: none
- reason-category: 2
- concealment: clear
- deformation: category pressure / none primary certified
- DO-orient: truth-seek
- live noetic burden: composition / dependence pressure on divine attributes
- current bounded operator: lexical / category discipline on "composition" and "dependence"
- held: full attribute exposition; source-comparison held
- source-status/noetic-frame: no public source-context release; selected operative frame internal
- gate/release decision: release bounded lexical/category correction; hold full exposition

### Layer B — bounded governed response
#### Hidden Premises
- Conceptual distinction is being treated as separable composition.
- "Depends on" is being used across senses without warrant.

#### Burden / Operation 1
##### Core Formulation
The deformation is a category-pressure move: real predication is collapsed into separable
part-composition, then dependence is imported through that collapse. The restoration vector
is lexical/category discipline: keep conceptual distinction, separable composition, and
ontological dependence in their proper order.

##### Bounded Response / operative submoves
Operative submove. Target: "composition." Operation: split separable parts from conceptual
distinction. Result: distinguishing knowledge from power does not entail separable parts.

Operative submove. Target: conceptual distinction -> ontological dependence. Operation:
test whether "depends on" is being used in one sense. Result: the equivocation is exposed.

##### TTP/operator trace
Trace: M9-predication-mode + diagnostic-render-contract.

### State/noetic re-read
- Cleared: composition / dependence pressure dissolved through the lexical and category split.
- Remaining input-anchored burdens: none in this prompt.
- Held routes rechecked: full attribute exposition and source-comparison remain held.
- Release status: closed for this input; no same-input eligible burden remains after the category correction.

### Restorative Response
The restored order is that real predication does not become dependency merely by being
conceptually distinguishable. The live pressure has been narrowed to its category mistake.

### Closing Formulation
What cleared is the composition-dependence inference; what remains held is broader attribute
exposition. The governed takeaway is that the objection no longer follows from the terms it used.

## Default-Mode Worked Example — Submove Boundary

**Input.** "The Satanic Temple's tenets are more humane than a God who hides himself,
condemns people to hell, and demands worship."

### Burden-Cycle 1
#### Layer A — Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: PF-10 moral protest / PF-2 evidentialist demand
- reason-category: 3
- concealment: clear; identity-performance not certified
- deformation: imported moral criterion as tribunal
- DO-orient: mixed moral-protest / evidential demand
- live noetic burden: imported moral tribunal judging divine action / worship-worthiness
- current bounded operator: imported moral tribunal authority test with subordinate hiddenness and punishment submoves
- held: broad punishment doctrine; pastoral expansion; interior motive certification
- source-status/noetic-frame: cited tenets marked as opponent-position internally; no public source-context support
- gate/release decision: release tribunal test and subordinate submoves; hold broad doctrine and pastoral expansion

#### Layer B — bounded governed response
##### Hidden Premises
- A compassion/autonomy criterion is being treated as an unquestioned tribunal over divine action.
- Hiddenness and punishment are functioning here as supports for that tribunal, not as separate burden-cycles.

##### Burden / Operation 1
###### Core Formulation
The governing deformation is criterion import: the objection installs a moral tribunal and
then judges worship-worthiness through it. The noetic pattern is authority displacement; the
restoration vector is to test the tribunal before answering downstream doctrinal material.

###### Bounded Response / operative submoves
Operative submove. Target: criterion authority. Operation: test whether the imported
compassion/autonomy criterion has justified authority over divine action. Result: the
criterion cannot remain an untested tribunal.

Operative submove. Target: hiddenness as coercive-proof demand insofar as it supports the
tribunal. Operation: disambiguate guidance from coercive individualized proof. Result: the
hiddenness claim no longer props up the same worship-worthiness indictment.

Operative submove. Target: punishment/accountability insofar as it supports the tribunal.
Operation: narrow the accusation to hujjah/accountability and hold broad punishment doctrine.
Result: the response blocks the claim that mere non-belief has been shown to be the premise.

###### TTP/operator trace
Trace: FPD + M1 + output-release.

#### State/noetic re-read
- Cleared: imported moral tribunal exposed; hiddenness and narrow accountability handled only
  as subordinate supports for that tribunal.
- Remaining input-anchored burdens: none newly licensed in this prompt.
- Held routes rechecked: broad punishment doctrine and pastoral expansion remain held.
- Release status: closed for this input unless a later prompt supplies a burden not already handled as a submove.

#### Restorative Response
The restored order is that mercy, guidance, accountability, and worship-worthiness cannot be
judged from an imported tribunal that has not itself been warranted. The operation landed only
that tribunal test; it did not release the held doctrine.

#### Closing Formulation
What cleared is the borrowed tribunal's authority; what remains held is broader punishment
doctrine and pastoral expansion. The governed takeaway is that the objection must first justify
its criterion before it can use hiddenness or punishment as proof against worship-worthiness.

This example instantiates the submove boundary: hiddenness, punishment/accountability, and
source-status can be operative submoves under the same governing burden. They become new
burden-cycles only after state/noetic re-read shows they remain live as distinct input-anchored
burdens rather than supports already handled inside the tribunal operation; they are not a
separate recursion merely because they were mentioned.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/output-release.md` | Governs what may be released before this file governs how it appears |
| `references/diagnostics/framework-pipeline.md` | Operative pipeline audit surface; bounded render sits here in the architecture |
| `references/diagnostics/recursive-state-transitions.md` | Canonical abstract owner for the post-render STOP / HOLD / RECURSE / PARTIAL decision |
| `references/diagnostics/case-state-schema.md` | `[Case State]`, `[Source Basis]`, `[Restoration Trace]` block schemas |
| `references/diagnostics/diagnostic-ir.md` | Internal Diagnostic IR and dispatch gate; default render derives from it but does not print it raw |
| `references/diagnostics/anti-patterns.md` | Failure examples for render cosplay, raw machinery leakage, and noetic-frame/source-status violations |

<!-- END_SOURCE: diagnostic-render-contract -->
