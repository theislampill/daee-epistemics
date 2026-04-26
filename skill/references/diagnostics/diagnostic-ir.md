---
id: diagnostic-ir
module_class: governance
canonical_path: skill/references/diagnostics/diagnostic-ir.md
contract_version: "0.2.3.0"
load_when:
  - any substantive engagement requiring routing — IR is not optional
routing_effects:
  - gates all module dispatch before any content module loads
emits:
  - routing_gate
catalogue_registered: false
---

# Diagnostic IR - Dispatch Gate and Typed Intermediate Representation

This file defines the complete typed state that must be formed before any content module is dispatched. It sits between the workflow layer (routing procedure) and the metaphysical-architecture layer (what is being restored). Its purpose is twofold:

1. Gate module dispatch. Dispatch is blocked until the mandatory minimum fields are populated and consistency checks pass.
2. Make routing auditable independently of prose quality.

The IR is not a retrospective record. Writing the IR after the response is cosmetic compliance. The
initial IR must govern dispatch before content release; the `post_render_gate` then refreshes that
same live control surface after a bounded move and before closure. If the initial IR cannot be
formed because mandatory fields cannot be populated, the correct action is Stop-4, not a response
with a post-hoc IR.

The IR composes fields from several sources:

- Case-state fields from `references/diagnostics/case-state-schema.md`
- Claim-level and pattern-profile fields from `references/diagnostics/pattern-profiling.md`
- Reason-category fields from `references/diagnostics/reason-disambiguation.md`
- Backbone predicate emissions from `references/diagnostics/arabic-backbone-predicates.md`
- Foreign-premise detection from `references/diagnostics/foreign-premise-detection.md`
- Prophetic discourse neutralization from `references/diagnostics/prophetic-discourse-neutralization.md`
- Philosophical-usurpation fields from `references/case-library/philosophical-usurpation.md` when active
- Architectural layer disruption from `references/metaphysical-architecture.md`
- P7 stop status from `references/procedures/P7-restoration-stops.md`
- Routing-precedence state from `references/diagnostics/routing-precedence.md`

---

## DSL-IR as Audited Formalization Layer

The Diagnostic IR is the repo's canonical audited formalization layer. It is where the live
noetic structure becomes actionable: claims, criteria, grounding relations, testimonial posture,
interpretive filters, held routes, and restoration target are rendered into one governable state
before any content release.

This formalization does not claim that the whole structure is exhausted by a pure proposition
graph. Grounding relations may be read graph-like, and often locally DAG-like, but the audited
control surface must also carry weighting, suppression, underdetermination, semantic holds,
register holds, and release permissions.

Meta-noetic memetics becomes operational here through fields such as `Foreign premise`,
`Upstream findings`, `Claim-level`, `Pattern-profile`, `Concealment mode`, `DO-orient`,
`What is withheld and why`, and `What remains live`. Those fields do not replace the repo's
existing owners; they make their dynamic interaction auditable by tracking docking, tribunal
installation, semantic capture, defensive persistence, and the collapse radius that follows when
a load-bearing node is cleared.

**Operationalization rule:** Meta-noetic memetics does not add a new routing pass. It is the
explanatory frame for the already-named dynamics. Its live IR surface is:

- `Foreign premise` and `Upstream findings`: tribunal-installation, criterion-smuggling, semantic-capture moves
- `Claim-level` and `Pattern-profile`: governing PF overlay and higher-order burden when these change routing or sequencing
- `Concealment mode`: how recognition is being suppressed
- `What is withheld and why`, `What remains live`, and `Post-render gate`: held routes, collapse radius, refreshed-state recheck, and the forced re-entry judgment after a load-bearing node is cleared

**Negative rule:** When the concept "meta-noetic memetics" is invoked in a response without any
of the above fields carrying a live read (no tribunal-installation in `Upstream findings`, no
active PF overlay, no collapse-radius note in `What remains live`), the concept is being used
decoratively. Decorative use is the anti-pattern named in
`references/diagnostics/anti-patterns.md §Higher-Order Vocabulary Theater`.

---

## Gate Protocol - Required Before Module Dispatch

Before any content module is dispatched, the following checks must pass in order. If any check fails, dispatch is blocked; the blocking condition is named explicitly rather than silently resolved.

**Gate Check 1 - Mandatory minimum fields populated.**
All pre-dispatch fields in the mandatory minimum, plus any live conditional mandatory fields, must be populated before module dispatch. `Post-render gate` is mandatory for the complete pass record, but it is populated after the bounded restorative move and before closure. Fields that cannot be populated because the basis is too thin route to Stop-4, not to a forced read.

**Gate Check 2 - Consistency rules pass.**
None of the invalid combinations may be present. An IR with an invalid combination is a misread. Re-run Phase 2 before dispatching.

**Gate Check 3 - Routing-precedence suppression rules applied.**
Apply `routing-precedence.md` suppression rules S-1 through S-8. If any suppression rule fires, the routing gate is blocked for the operation that rule suppresses, regardless of how strong the NS or deformation read is.

**Gate Check 4 - P7 stops checked.**
Each P7 stop, when triggered, blocks the corresponding content operation. Check all five stops before dispatch.

**Gate Check 5 - Architectural integrity check.**
The `Restoration target` field must name a specific epistemic layer (`fitrah`, sound reason, authentic transmission, inferential argument) or ontological distinction (`creator-creation`, `transcendence-immanence`, `prophetic-authority`) from `metaphysical-architecture.md`. Also check that no `kernel-thesis.md` violation signature is present.

**Gate Check 6 - Route cleared for content.**
After checks 1-5 pass, confirm the concealment x orientation matrix in `case-state-schema.md`
shows what is deployable now in Layer B. If register-hold applies, the matched content module
is held from direct deployment, not erased from the complete audit record.

Only after all six checks pass does module dispatch proceed.

**Gate trigger tracing:** When any check fires and blocks dispatch, record which check
triggered the block using the `Gate trigger` field in the IR (e.g., `check 3 — S-2`,
`check 4 — Stop-2`, `check 6 — register-hold`). When the gate is `open`, omit the field.
This makes routing failures auditable without re-running the full gate protocol: the IR
record names the blocking check, not just the resulting gate state.

---

## Full IR Schema

```text
[Diagnostic IR]

--- Workflow Layer ---
Case family:
Claim-type:                          # logical | metaphysical | moral | historical | transmission | phenomenological | authority
Claim-level:                        # first-order | meta-epistemic | meta-ontological | meta-noetic | cross-level
Pattern-profile:                    # PF-1 ... PF-12 | none
NS code:                             # NS-1 through NS-12, or provisional
Deformation:                         # primary [| secondary], in intervention order
Concealment mode:                    # clear | irad | juhud | inkar | istikbar | nifaq | mode-? | compound
DO-orient:                           # truth-seek | identity-perf | autotelic | zann-mode | mixed
RT marker (if active):               # RT-1 | RT-2 | RT-3 | RT-4 | none; keep `none` for ḥadīth-authentication cases unless a separate Qur'anic RT family is also live
Read status:                         # dominant | distributed | underdetermined
Confidence:                          # strong | provisional | low
Alignment state:                     # blocked | tribunal-loosened | frame-cleared | recognition-surfaced | alignment-advanced
Recognition strength:                # none | weak | medium | strong
Continuation eligibility:            # not-assessed | blocked | eligible-on-refresh
P7 stops active:                     # Stop-1 | Stop-2 | Stop-3 | Stop-4 | Stop-5 | none
Routing gate:                        # open | V2-required | deformation-first | semantic-discipline-required | register-hold | stop-condition
Gate trigger:                        # omit when gate is open; when gate fires: check [1–6] + rule or stop id, e.g. "check 3 — S-2" or "check 4 — Stop-2"
Matched modules:                     # current-pass, case-state-justified coordination only
Prohibited moves:                    # list any PM from routing-precedence or do-attribute-precision

--- Architectural Layer ---
Reason-category:                     # 1 (sound) | 2 (corrupted) | 3 (pseudo-neutral) | 4 (inherited)
Backbone predicates active:          # list true predicates from arabic-backbone-predicates.md
Foreign premise:                     # detected [premise, source, functional role] | none-detected | uncertain
Upstream findings:                   # criterion-import | tribunal-installation | transmission-demotion | semantic-neutralization-recontenting | semantic-neutralization-evacuation | lexical-ontological-trap
Philosophical usurpation:            # type [A | B | C | D] + active telltale features | none
Architectural layer disrupted:       # fitrah | sound-reason | authentic-transmission | inferential-route | transcendence-immanence | prophetic-authority | none
Ontological disorder:                # category-mistake | illicit-analogy | equivocal-predication | composition-panic | person-multiplicity-conflation | perfect-being-usurpation | none
Restoration target:                  # what noetic faculty, epistemic ordering, or ontological distinction is being cleared or re-established
Structural pattern print:            # optional; compact local pattern description when PF code alone would lose practical framing
Load-bearing node:                   # optional; criterion, authority rule, semantic hinge, category-set, or noetic blocker currently carrying the pressure
Collapse radius:                     # optional; downstream claims/routes that depend on the load-bearing node and must be re-evaluated when it clears
Intervention target:                 # optional; the bounded operation that clears the load-bearing node
Framing notes:                       # optional; internal renderer constraints preventing citation dump, argument bank, or wrong-family release

--- Output Governance ---
                                  # Canonical Layer A / Layer B definition: `SKILL.md §V.A — Two-Layer Output Contract`.
                                  # Output-governance fields govern Layer B only.
                                  # Layer A always preserves the complete diagnostic output.
Source basis:                        # anchored | synthesis | inference | speculative - per claim
Inference boundary active:           # yes | no
Output shape:                        # Layer B only: content | relational | maieutic | invitational | single-response | held-pending
Next move:                           # one specific action the response takes next
What is withheld and why:            # Layer B hold only; never used to omit Layer A diagnosis or matched modules
What remains live:                   # open differentiators, unresolved axes, or questions the next exchange must answer
Post-render gate:                    # mandatory State Refresh / Re-Entry Gate before STOP, HOLD, RECURSE, or PARTIAL
  Cleared this pass:
  Remaining live distortions:
  Held routes rechecked:
  Newly released routes:
  Next eligible pass:
  Recursion decision:                 # STOP | HOLD | RECURSE | PARTIAL
```

---

## Field Rules

Compression rule: the IR is not a checklist to be filled performatively. Populate only fields with operative content, except for mandatory control fields such as `post_render_gate`, which must record the governance decision even when its result is `none` / STOP.

Noetic-object rule: populate the IR as a state of the structure, not as a paraphrase of the
discourse. The point is to formalize what configuration is live, what governs release now, and
what depends on what - not merely to restate the surface wording.

Concealment mode is mandatory. Use `clear` when no active concealment mode is positively read.
Use `mode-?` when the axis remains unresolved. Blank values, em dashes, or placeholders such as
`none confirmed` are invalid because they erase the difference between "resolved absent" and
"still unread."

**Mandatory minimum**

For any substantive response claiming to have done V1, the following fields must be populated:

- Case family
- Claim-type
- Deformation
- Concealment mode
- DO-orient
- Read status
- Confidence
- Alignment state
- Recognition strength
- Continuation eligibility
- P7 stops active
- Reason-category
- Routing gate
- Matched modules
- Restoration target
- Next move
- Output shape
- Post-render gate
- Claim-level
- Pattern-profile

`Post-render gate` is mandatory for a completed pass, not for initial dispatch. It is populated
after the bounded move and before STOP, HOLD, RECURSE, or PARTIAL is declared.

If these fields cannot be populated because the basis is too thin, the correct output is Stop-4 plus the specific missing differentiator.

**Conditional mandatory additions**

Populate these whenever their trigger is live:

- Internal IR discipline: in the validator-backed Diagnostic IR, `Claim-level` and `Pattern-profile` stay explicit even in routine cases. Use `Claim-level: first-order` and `Pattern-profile: none` when the higher-order and PF triggers have been checked and found inactive. Compression to omission is only for surfaced routine case-state, not for the internal IR.
- `Foreign premise` and `Upstream findings` when criterion import, tribunal installation, transmission demotion, or framework import is visible
- `Backbone predicates active` when trigger mapping in `references/diagnostics/arabic-backbone-predicates.md` calls for checks
- `Philosophical usurpation` when an imported framework is functioning as upstream tribunal
- `RT marker` when the live transmission pressure instantiates RT-1 through RT-4. Ḥadīth-authentication cases without a separate Qur'anic RT family keep `RT marker: none` and route through `references/diagnostics/hadith-authentication-epistemology.md`
- `What is withheld and why` when register-hold, semantic gate, or stop governance keeps a diagnosed downstream route from current deployment
- `What remains live` when live alternatives, held routes, a boundary-reset condition, or a load-bearing dependency with downstream collapse radius must stay visible
- `Alignment state`, `Recognition strength`, and `Continuation eligibility` whenever restoration progress, stop thresholds, or refreshed continuation are doing real routing work. In the validator-backed internal IR these fields should be explicit whenever a landed move, recognition judgment, or recurse-vs-stop decision is live.
- `Post-render gate` after every bounded restorative move and before any closing decision. It is mandatory even when the decision is STOP; STOP is invalid unless the gate has run.

**Optional structural framing fields**

The fields `Structural pattern print`, `Load-bearing node`, `Collapse radius`,
`Intervention target`, and `Framing notes` are optional IR fields. They do not add a
new routing pass and do not replace `claim_level`, `pattern_profile`, NS/DO/RT routing,
FPD, V2, M9, V10, P7, or routing-precedence suppression. They are a local descriptive
layer used only when the existing fields would otherwise lose the practical framing that
controls sequencing and release.

Populate them only when all of the following hold:

- `Claim-level` is `meta-epistemic`, `meta-ontological`, `meta-noetic`, or `cross-level`.
- The input is thick enough to identify a real structure rather than a topic label.
- The pattern changes routing, sequencing, suppression, release discipline, or renderer constraints.
- PF code alone is too coarse to preserve the local load-bearing node and what is held behind it.

Do not populate them on thin input, as decorative terminology, as public-output boilerplate,
or as a substitute for module ownership. `Structural pattern print` names the practical
shape; `Load-bearing node` names what must clear first; `Collapse radius` names what
depends on that node; `Intervention target` names the next bounded clearing operation;
`Framing notes` tells the renderer how not to mishandle the case.

Typical framing notes are prohibitions, not miniature arguments:

```text
do not answer as fiqh detail until imported criterion is exposed
do not use external scripture as a clean independent foundation
do not treat Arya Samaj as Advaita
do not treat anatta as simple materialism
do not debate kashf occurrence before jurisdiction is classified
do not collapse abuse wound into doctrine
avoid citation bank; use source-use discipline only if prooftexts become live
```

These notes are internal constraints. They appear in public output only when the render
contract permits a diagnostic or audit-style response.

**Current-pass activation rule**

- `Matched modules` records only the case-state-justified coordination active in the present pass.
- Diagnosed downstream content that is held by register, semantic, or stop governance remains explicit in Layer A through `What is withheld and why` / `What remains live`; it is not silently dropped, but it is also not treated as simultaneously active.
- **Three-way activation partition:** Absence from both `Matched modules` and `What is withheld and why` means the module was never triggered by the current case-state — it is not in scope given the diagnostic read. Presence in `What is withheld and why` alone means the module was triggered but blocked by governance. Presence in `Matched modules` means the module is active in this pass. These three states must not be collapsed; an auditor must be able to distinguish "never in scope" from "triggered and suppressed" without re-running the diagnostic gate.
- **Ghost-load prohibition:** A `matched_modules` entry without a corresponding `source_basis` entry with `source_kind: "module"` and `module_id` matching the entry's `id` is a ghost-load: the file was loaded but did not demonstrably govern any output claim or routing decision in this pass. Ghost-loads are gate-integrity failures equivalent to fabricated activation and must be corrected before dispatch — either by adding the missing `source_basis` entry (naming the specific claim or routing fork the module governed) or by moving the module from `matched_modules` to `What is withheld and why` with an explicit reason.
- `Next move` names one live move only. It is not a queue of later modules.
- When a load-bearing premise, criterion, or authority node has been cleared, `What remains live`
  should mark any dependent claims whose support has collapsed or whose status now requires
  re-evaluation before further routing.
- When Stop-2 fires or a move has landed, boundary reset applies: later activation begins from a fresh V1-governed round rather than from carried-forward module state. A fresh round may be opened by a later reply or by a clear differentiating signal within the same message, its accompanying propositions, or its entailments, but only when the refreshed state still shows an unmet restoration target and no stop, register-hold, or semantic gate bars the next move.

**Post-render State Refresh / Re-Entry Gate**

After every bounded restorative move, and before any closing or STOP decision, the IR must run
`post_render_gate`. The gate asks:

1. What was cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. Is there a next eligible pass?
6. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

Decision semantics:

- `STOP` is valid only if the gate has run, no live distortion remains, no held route has become newly eligible, and `next_eligible_pass` explicitly records `none`.
- `HOLD` is valid only when remaining material exists but its release signal is absent because a stop, register-hold, semantic gate, thin-basis rule, or other hard rail still blocks it.
- `RECURSE` is required when another live distortion remains in the same input, or when a held route becomes newly eligible after the current pass clears its blocker.
- `PARTIAL` is required when token, tool, or interaction limits prevent completion while recursive pressure remains. Do not emit a false STOP in that condition.

The gate is not a new routing pass. It is the post-render enforcement point that makes the
validated IR remain live after the response has made its bounded move.

**Recursive-state model:** `references/diagnostics/framework-pipeline.md §Recursive State-Transition View` is the canonical owner of the STOP / HOLD / RECURSE / PARTIAL state model. The fields `continuation_eligibility`, `alignment_state`, `recognition_strength`, and `post_render_gate` are this IR's typed carriers of that model. State-transition semantics and recursive re-entry conditions are defined in `framework-pipeline.md`; this section governs only how those states are represented in the IR record.

**State-carry partition:** The consolidated table of what χ (state refresh) retains, resets, and re-evaluates across a pass boundary is in `references/diagnostics/framework-pipeline.md §Recursive Layer — State Carry Table`. The boundary-reset rule for matched modules after Stop-2 and the current-pass activation rule above are prose expressions of that same partition.

**Acceptance-state rules**

- `Alignment state` keeps restoration progress typed. Use `blocked` when the governing filter still controls the case; `tribunal-loosened` when the imported criterion has visibly lost its neutrality claim; `frame-cleared` when the subject can now examine signs, revelation, or transmission without the old filter governing; `recognition-surfaced` when a landed move has produced medium or strong visible uptake; `alignment-advanced` only when positive recognition and willingness to inhabit the restored order are visibly present.
- `Recognition strength` must track the stop threshold rather than tone alone. `weak` covers politeness, irritation, surprise, silence, or rhetorical concession without state-shift; `medium` covers local consequence admission, reflective pause, or premise-examination; `strong` covers explicit blocker removal, accurate restatement, sincere next-questioning from the cleared frame, or a visible register shift into inquiry.
- `Continuation eligibility` governs post-landing release. Use `not-assessed` before the question is live; `blocked` when a stop, hold, gate, or satisfied target forbids more release; `eligible-on-refresh` only when a fresh differentiating signal has reopened V1, the restoration target remains unmet, and no stop, register-hold, or semantic gate remains live for the next move.

  **Positive termination:** When the restoration target is met and `alignment_state` is
  `alignment-advanced` with `recognition_strength: strong`, set
  `continuation_eligibility: blocked` and record `What remains live: none — restoration
  target satisfied`. This sub-type of `blocked` marks restorative completion, not a
  governance stop. It must be distinguished from `blocked` under an active stop condition
  so that audits can confirm the framework terminated correctly rather than prematurely.

**State transition table** — the three acceptance-state fields interact as follows. This
table makes the forward direction explicit: given alignment state and recognition strength,
what does continuation eligibility resolve to? Derived from the prose rules above; does not
introduce new semantics.

| `alignment_state` | `recognition_strength` | → `continuation_eligibility` |
|-------------------|------------------------|------------------------------|
| `blocked` | any | `blocked` |
| `tribunal-loosened` | `weak` or `medium` | `blocked` |
| `tribunal-loosened` | `strong` | `eligible-on-refresh` (if target unmet); `blocked — satisfied` (if target met) |
| `frame-cleared` | `weak` | `blocked` |
| `frame-cleared` | `medium` | `eligible-on-refresh` (if target unmet); `blocked` (if no fresh signal yet) |
| `frame-cleared` | `strong` | `eligible-on-refresh` (if target unmet); `blocked — satisfied` (if target met) |
| `recognition-surfaced` | `medium` or `strong` | `eligible-on-refresh` (if target unmet) |
| `recognition-surfaced` | `weak` | `blocked` |
| `alignment-advanced` | `strong` | `blocked — satisfied` |

All `eligible-on-refresh` outcomes additionally require: a fresh differentiating signal has
reopened V1, and no active stop, register-hold, or semantic gate remains live for the next
move.

**Consistency rules**

The following inconsistencies are invalid:

- `Read status: underdetermined` + `Confidence: strong`
- `Concealment mode: juhud` + `Output shape: content`
- `P7 Stop-1 active` + `Output shape: content`
- `DO-orient: identity-perf | autotelic` + `Output shape: content`
- `Routing gate: V2-required` + `Matched modules: [any content module]`
- `Routing gate: semantic-discipline-required` + `Matched modules: [any doctrinal case file or attribute-content release]`
- `Routing gate: register-hold` + missing `What is withheld and why`
- `Routing gate: semantic-discipline-required` + missing `What is withheld and why`
- `Routing gate: stop-condition` + missing `What is withheld and why`
- `DO-orient: identity-perf` + `Matched modules: [any doctrinal case file]`
- `Reason-category: 3 or 4` + `Routing gate: open`
- `Concealment mode: anything other than clear` + `Output shape: content`. Register-hold governs Layer B whenever concealment remains live.
- `Claim-level: meta-epistemic | meta-ontological | meta-noetic` + `Matched modules: [first-order case file only]`. Higher-order burdens must clear before first-order dispatch.
- `Upstream findings` contains `semantic-neutralization-recontenting`, `semantic-neutralization-evacuation`, or `lexical-ontological-trap` + `Routing gate: open`
- `Matched modules` includes anticipated downstream modules or reserve owners not governing the current pass
- `P7 Stop-2 active` + `Next move` advertises another argumentative sequence rather than a boundary reset / one bounded question
- `Alignment state: alignment-advanced` + `Recognition strength` anything other than `strong`
- `Continuation eligibility: eligible-on-refresh` + missing `What remains live`
- `NS code: NS-6` + ontological burden live + generic restoration target. NS-6 ontological cases require a school-specific restoration target (`ḥudūth/khalq` distinction for the Muʿtazilī form; `kalām nafsī` doctrine for the Ashʿarī form), not a generic `bilā kayf` or generic foundationalist target.
- `NS code: NS-6` + ontological burden live + `Backbone predicates active` omits `O-1` and `C-1`. When NS-6 and the case involves divine attributes or speech, those predicates are minimum checks.
- `Structural pattern print` present + `Pattern-profile` absent or unset. Pattern print is subordinate to PF discipline; use `Pattern-profile: none` only when no PF overlay governs.
- `Structural pattern print` present + no routing, hold, release, or framing consequence. Pattern print without consequence is pattern theater.
- `Load-bearing node` present + downstream content released before the node is addressed. This violates upstream-node priority.
- `Framing notes` used to introduce new coverage content, prooftexts, or citations rather than to constrain release. Framing notes are not a citation bank.
- Source-audit-derived tradition label used as the route while the structural node remains untyped. "Jewish", "Hindu", "Sufi", or "Buddhist" is not itself a routing owner.
- One upstream node cleared + all downstream material dumped at once. Refresh state and release only the next bounded move.
- Missing `Post-render gate` after a bounded restorative move. STOP, HOLD, RECURSE, and PARTIAL decisions are invalid until the gate has run.
- `Post-render gate: recursion_decision: STOP` while `remaining_live_distortions` names a live distortion, `newly_released_routes` is non-empty, or `next_eligible_pass` is anything other than `none`.
- `Post-render gate: recursion_decision: HOLD` while the remaining material has a present release signal and no stop, register-hold, semantic gate, thin-basis rule, or other hard rail blocks it.
- `Post-render gate: recursion_decision: RECURSE` while `next_eligible_pass` is `none`, or while the response fails to release the next eligible bounded pass.
- `Post-render gate: recursion_decision: PARTIAL` without naming the remaining live distortion and the next eligible pass that limits prevented.

An IR with any of the above combinations has drifted.

---

## Compressed Form

For cases where a subset of fields is sufficient, the compressed form may be used:

```text
[IR - compressed]
Case: [family] | Claim: [type @ level?] | Pattern: [PF-x | none] | NS: [code] | Def: [code] | Conc: [mode] | Orient: [DO] | Gate: [routing gate] | Align: [state] | Rec: [strength] | Continue: [status] | Module: [matched] | Target: [restoration] | Next: [one move] | Post: [STOP|HOLD|RECURSE|PARTIAL; next=...]
```

The compressed form is not acceptable when architectural-layer fields are active. If the
level is omitted in compressed form, it means first-order after higher-order triggers
have been checked, not an unexamined blank.

---

## How the IR Prevents Cosmetic Compliance

Specific failure modes:

- **Cosmetic V1 compliance:** the response says V1 was run but the routing gate remains open while orientation or upstream blockers still prevent content.
- **Cosmetic framework-clearing:** the response names V2 but still loads content into the unreconstituted filter.
- **Cosmetic register acknowledgment:** the response acknowledges grief or register-hold but still outputs propositional content.
- **Current-pass blur:** the response advertises a queue of downstream modules rather than the coordination actually governing this pass.
- **Output-layer collapse:** the response notes `irad` or another register-hold and therefore omits the structural diagnosis from the complete output, leaving technique without the diagnostic architecture that justified it.
- **Held-route preview:** a stop or register-hold is named, but Layer B still previews the held doctrinal substance or future module chain.
- **Architectural drift:** the response satisfies workflow checks but states the restoration target argumentatively rather than restoratively.
- **Semantic-bypass compliance:** semantic neutralization or a lexical-ontological trap is active, but doctrinal content is released anyway. The IR catches this by requiring `semantic-discipline-required`.
- **Pattern-print theater:** the response names a structural pattern but does not identify the load-bearing node, intervention target, held downstream material, or existing route.
- **Argument-bank substitution:** the response treats a source-audit-derived topic as permission to list arguments, prooftexts, or citations before the live authority rule, criterion, or semantic blocker has been typed.

---

## Source-Audit Structural Validation Notes

These notes validate structural framing only. They do not create new coverage claims,
new case-family owners, or permission to release comparative-religion content. Each
fixture names an internal pattern print and the existing routes that govern the next
move.

### 1. DO-15 moral objections

```text
Structural pattern print: validation inversion / Level A vs Level B collapse / imported moral tribunal
Load-bearing node: moral criterion and validation order
Collapse radius: detailed fiqh, hudud detail, gender jurisprudence detail, slavery-history monograph
Intervention target: expose the criterion, preserve real fitri moral recognition, test whether the specific ruling under full conditions violates the internal criterion
Framing notes: do not deny moral perception; do not capitulate to the imported tribunal; do not answer with "rarely applied" as the whole response; do not defend historical abuse as shari'ah
Existing route: FPD + philosophical-usurpation Type D + V2 + existing DO-15
Held: detailed fiqh and legal-history expansion
Must not dump: citation bank, fiqh monograph, apologetic minimization, abuse-as-doctrine defense
```

### 2. Sufi kashf / tariqah authority

```text
Structural pattern print: authority inversion / kashf-as-tribunal / charismatic authority as epistemic override
Load-bearing node: authority jurisdiction of kashf, shaykh, or tariqah relative to revelation
Collapse radius: broad Sufism taxonomy, contested-practice fiqh, anti-Sufism polemic
Intervention target: classify whether the experience or authority claim has jurisdiction over revelation
Framing notes: do not debate whether the event occurred before jurisdiction is classified; separate authority wound from authority tribunal
Existing route: FPD + philosophical-usurpation + NS-8/P7 as needed + M7/M9 if vocabulary governs
Held: Sufism owner content, practice adjudication, global attack/defense of Sufism
Must not dump: anti-Sufism polemic, tariqah history, contested practice rulings
```

### 3. Jewish Torah-completeness / final-prophethood

```text
Structural pattern print: closed-canon veto / selective scriptural arbitrage / prior-recognition dispute
Load-bearing node: whether Torah, canon, or rabbinic closure functions as veto over later divine speech
Collapse radius: biblical prooftext use, comparative-prophethood content, Jewish owner content
Intervention target: classify impossibility, authority, evidence, canon, interpretation, or identity/covenant wound before prooftexts
Framing notes: do not make external prooftexts the foundation; do not treat Jewish and Christian objections as identical
Existing route: FPD + DO-14/V10/RT + comparative-prophethood/DO-10 as appropriate
Held: biblical prooftext dump, broad Judaism coverage, new Jewish owner content
Must not dump: lists of prooftexts or citations before source-use discipline
```

### 4. Arya Samaj Qur'an critique

```text
Structural pattern print: external criterion as tribunal / Vedic-reformist reason claim / Satyarth-Prakash-style polemical standard
Load-bearing node: criterion used to judge Qur'an, prophecy, divine attributes, resurrection, or law
Collapse radius: verse-by-verse Qur'an defense, Hindu owner content, exact Sanaullah citations
Intervention target: disclose whether "reason/common sense" is sound reason or a school-bound polemical criterion
Framing notes: do not treat Arya Samaj as Advaita; do not quote noisy Urdu OCR as exact source
Existing route: FPD + V2 + reason-disambiguation + M9 if divine predication is live + RT if source authority becomes central
Held: Hindu Arya owner, Sanaullah exact quotations, broad Hinduism coverage
Must not dump: verse defenses, OCR citations, "Hinduism covered" language
```

### 5. Advaita

```text
Structural pattern print: non-duality / illusion ontology / Creator-creation collapse / higher-lower truth tribunal
Load-bearing node: whether nondual ontology is functioning as the upstream category-set over Islamic tawhid
Collapse radius: ordinary polytheism response, Advaita owner content, Hinduism coverage claim
Intervention target: distinguish Islamic tawhid, monism/nonduality, and mystical or poetic language before content release
Framing notes: do not collapse Advaita into popular idol worship; do not claim source-audited Advaita coverage
Existing route: M9 + metaphysical-architecture + philosophical-usurpation if nondual ontology is installed as tribunal
Held: Advaita owner content and broad Hinduism coverage
Must not dump: generic idol-worship answer when nondual ontology is live
```

### 6. Buddhist anatta / impermanence

```text
Structural pattern print: self-negation / identity-continuity pressure / two-level discourse / impermanence category pressure
Load-bearing node: whether the claim denies enduring subjecthood, denies independent ego, or uses therapeutic anti-essentialism differently from metaphysical denial
Collapse radius: Buddhist owner content, primary Buddhist-source claims, broad Buddhism coverage
Intervention target: clarify self, nafs, ruh, person, continuity, moral responsibility, and created dependence before response
Framing notes: do not treat anatta as simple materialism; do not equate Islamic nafs with an autonomous self-existent ego
Existing route: M9 + V9 + metaphysical-architecture as appropriate
Held: Buddhist anatta/impermanence owner content and broad Buddhism coverage
Must not dump: primary Buddhist-source claims or generalized Buddhism rebuttal
```

---

## Connection to Framework Pipeline

`references/diagnostics/framework-pipeline.md` shows the structural branching of the canonical pipeline. `references/diagnostics/routing-precedence.md` specifies the decision rules at each branch point. This file is the gate and the typed state produced at the end of V1 Phase 2 - the check that must be passed before module selection occurs.

**IR-to-surfaced-output derivation:** The field-by-field mapping from internal IR fields to
surfaced `[Case State]` output fields is in
`references/diagnostics/case-state-schema.md §IR Derivation Map`. Use that table to verify
that a surfaced case-state is derived from the validated IR rather than improvised.

---

## Failure Tests

This file has not governed the response if any of the following is true:

- The IR was written after the response.
- The restoration target names what argument is being won, not what epistemic faculty or ordering is being restored.
- Mandatory minimum fields are empty but the IR is presented as complete.
- A suppression rule was active but the corresponding module was still dispatched.
- A consistency-rule violation is present but the response proceeded anyway.
- A semantic-discipline blocker was present but doctrinal content still released.
- The IR carried the previous round's matched modules forward after Stop-2 or another boundary reset without re-running V1.
- A bounded restorative move rendered, then the response closed without populating `post_render_gate`.
- `recursion_decision: STOP` was emitted before the gate rechecked held routes and confirmed `next_eligible_pass: none`.
