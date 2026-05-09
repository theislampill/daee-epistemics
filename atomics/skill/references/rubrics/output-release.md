---
id: output-release
module_class: governance
canonical_path: skill/references/rubrics/output-release.md
contract_version: "0.3.2.0"
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
For hard, compound, or deformed recursive cases, the next bounded pass begins with a fresh
compact Layer A for that burden before Layer B resumes. Layer A is the live diagnostic control
state; Layer B is the governed intervention. This keeps continuation from becoming a checklist
or route queue without renewed noetic assessment.
`R(H,Delta)` must judge the refreshed state: continue, hold/defer, skip as no longer live,
mark PARTIAL, request bounded reroute when the live state materially changed, or close when
no input-anchored burden remains. A planned continuation queue proposes order; it does not
override this state-transition judgment.

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
Hiddenness, punishment/accountability, source-status, source-worldview, consequence tracing,
and identity-stabilization may belong to the same governing burden only as distinct bounded
submoves. Do not consolidate active TTP/operator functions into one generic operation block.
Restoration synthesis and any pastoral note release only after the active burden lands and
state re-read licenses closure, HOLD, PARTIAL, or the next input-anchored burden.
Identity-stabilization or source-status that is live and input-anchored must feed the
restoration vector or practitioner instruction; it must not remain a diagnostic orphan, and it
must not become speculative interior judgment.

Live-burden boundary is governed by the noetic burden being cleared. Imported-criterion tribunal
testing, hujjah/accountability correction, and guidance-as-coercive-proof correction can all be
Burden-1 `s` when they serve the same worship-worthiness tribunal question. Do not split those
internal operators into Pass 1 / Pass 2 / Pass 3 unless `R` has already landed Burden 1 and
licensed a genuinely new noetic aspect.
Multi-burden does not mean multi-recursion by default:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
They become separate burden-cycles only if `R` shows a new input-anchored `B` not already handled
as `s`. But `s` remains plural and operative: each active TTP receives a distinct target,
operation, and result before `Land(B)`.

Before a fourth major operative submove is released inside one Layer B, run the submove
saturation gate from `recursive-state-transitions.md`. If the next move changes target-family,
claim-level, source/noetic frame, claim cluster, or restoration vector, the current burden must
land and state must be re-read before the next burden is released. If the fourth move is merely
available rather than materially necessary, HOLD or PARTIAL rather than inflating Layer B. This
gate prevents argument dumping; it must not be used to erase a materially necessary TTP submove
or to demote a live identity/source-status implication into a label.

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
- default citation allowance is restricted to Qurʾān, Sunnah, and sound narrations from the
  Salaf, and any such use is directly referenced through an external source
- Qurʾānic or ḥadīth evidence quoted for operative work is formatted cleanly where practical:
  Arabic when useful, translation, source/reference, then its diagnostic or restorative function.
  Prefer precision texts that name the mechanism; do not add citation padding, and do not collapse
  a central revealed text into a long prose sentence.
- `Islamic scholar` and `Islamic scholarship` are not umbrella terms for kalām, falsafah, or
  later speculative-theological figures; use specific source-status labels instead.
- umbrella terms (`classical theology`, `the classical tradition`, `mainstream kalām`,
  `Ashʿarī/Māturīdī tradition`) are not used as if they named one operative authority on
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
submove saturation is not a merge license; active TTP/operator functions remain distinct or the output is PARTIAL
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
- Strong interior-classification verdict dumps such as `Concealment: iʿrāḍ primary`,
  `Deformation: hawā primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
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
