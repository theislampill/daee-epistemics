> role: dispatch gate and typed diagnostic intermediate representation - the constrained layer that module dispatch must pass through before any content module is loaded
> use when: any substantive engagement requiring routing; the IR is not optional for these cases
> do not use when: the task is a narrow conversational sub-answer with no case classification required
> output: a typed diagnostic state that gates module dispatch and serves as the auditable record of the routing decision

# Diagnostic IR - Dispatch Gate and Typed Intermediate Representation

This file defines the complete typed state that must be formed before any content module is dispatched. It sits between the workflow layer (routing procedure) and the metaphysical-architecture layer (what is being restored). Its purpose is twofold:

1. Gate module dispatch. Dispatch is blocked until the mandatory minimum fields are populated and consistency checks pass.
2. Make routing auditable independently of prose quality.

The IR is not a retrospective record. Writing the IR after the response is cosmetic compliance. If the IR cannot be formed because mandatory fields cannot be populated, the correct action is Stop-4, not a response with a post-hoc IR.

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
- `What is withheld and why` and `What remains live`: held routes and collapse radius after a load-bearing node is cleared

**Negative rule:** When the concept "meta-noetic memetics" is invoked in a response without any
of the above fields carrying a live read (no tribunal-installation in `Upstream findings`, no
active PF overlay, no collapse-radius note in `What remains live`), the concept is being used
decoratively. Decorative use is the anti-pattern named in
`references/diagnostics/anti-patterns.md §Higher-Order Vocabulary Theater`.

---

## Gate Protocol - Required Before Module Dispatch

Before any content module is dispatched, the following checks must pass in order. If any check fails, dispatch is blocked; the blocking condition is named explicitly rather than silently resolved.

**Gate Check 1 - Mandatory minimum fields populated.**
All fields in the mandatory minimum, plus any live conditional mandatory fields, must be populated. Fields that cannot be populated because the basis is too thin route to Stop-4, not to a partial IR.

**Gate Check 2 - Consistency rules pass.**
None of the invalid combinations may be present. An IR with an invalid combination is a misread. Re-run Phase 2 before dispatching.

**Gate Check 3 - Routing-precedence suppression rules applied.**
Apply `routing-precedence.md` suppression rules S-1 through S-7. If any suppression rule fires, the routing gate is blocked for the operation that rule suppresses, regardless of how strong the NS or deformation read is.

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
```

---

## Field Rules

Compression rule: the IR is not a checklist to be filled performatively. Populate only fields with operative content.

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
- Claim-level
- Pattern-profile

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

**Current-pass activation rule**

- `Matched modules` records only the case-state-justified coordination active in the present pass.
- Diagnosed downstream content that is held by register, semantic, or stop governance remains explicit in Layer A through `What is withheld and why` / `What remains live`; it is not silently dropped, but it is also not treated as simultaneously active.
- **Three-way activation partition:** Absence from both `Matched modules` and `What is withheld and why` means the module was never triggered by the current case-state — it is not in scope given the diagnostic read. Presence in `What is withheld and why` alone means the module was triggered but blocked by governance. Presence in `Matched modules` means the module is active in this pass. These three states must not be collapsed; an auditor must be able to distinguish "never in scope" from "triggered and suppressed" without re-running the diagnostic gate.
- `Next move` names one live move only. It is not a queue of later modules.
- When a load-bearing premise, criterion, or authority node has been cleared, `What remains live`
  should mark any dependent claims whose support has collapsed or whose status now requires
  re-evaluation before further routing.
- When Stop-2 fires or a move has landed, boundary reset applies: later activation begins from a fresh V1-governed round rather than from carried-forward module state. A fresh round may be opened by a later reply or by a clear differentiating signal within the same message, its accompanying propositions, or its entailments, but only when the refreshed state still shows an unmet restoration target and no stop, register-hold, or semantic gate bars the next move.

**Recursive-state model:** `references/diagnostics/framework-pipeline.md §Recursive State-Transition View` is the canonical owner of the STOP / PAUSE / RECURSE state model. The fields `continuation_eligibility`, `alignment_state`, and `recognition_strength` are this IR's typed carriers of that model. State-transition semantics and recursive re-entry conditions are defined in `framework-pipeline.md`; this section governs only how those states are represented in the IR record.

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

An IR with any of the above combinations has drifted.

---

## Compressed Form

For cases where a subset of fields is sufficient, the compressed form may be used:

```text
[IR - compressed]
Case: [family] | Claim: [type @ level?] | Pattern: [PF-x | none] | NS: [code] | Def: [code] | Conc: [mode] | Orient: [DO] | Gate: [routing gate] | Align: [state] | Rec: [strength] | Continue: [status] | Module: [matched] | Target: [restoration] | Next: [one move]
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
