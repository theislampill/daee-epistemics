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
P7 stops active:                     # Stop-1 | Stop-2 | Stop-3 | Stop-4 | Stop-5 | none
Routing gate:                        # open | V2-required | deformation-first | semantic-discipline-required | register-hold | stop-condition
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
- P7 stops active
- Reason-category
- Routing gate
- Matched modules
- Restoration target
- Next move
- Output shape

If these fields cannot be populated because the basis is too thin, the correct output is Stop-4 plus the specific missing differentiator.

**Conditional mandatory additions**

Populate these whenever their trigger is live:

- `Claim-level` when a higher-order burden is visible, when `cross-level` sequencing is needed, or when the IR is being emitted as the full audit record. If absent in a compressed routine case, treat the level as first-order only after higher-order triggers have been checked and found inactive.
- `Foreign premise` and `Upstream findings` when criterion import, tribunal installation, transmission demotion, or framework import is visible
- `Backbone predicates active` when trigger mapping in `references/diagnostics/arabic-backbone-predicates.md` calls for checks
- `Pattern-profile` when a recurring PF family is governing routing or cross-volume consolidation
- `Philosophical usurpation` when an imported framework is functioning as upstream tribunal
- `RT marker` when the live transmission pressure instantiates RT-1 through RT-4. Ḥadīth-authentication cases without a separate Qur'anic RT family keep `RT marker: none` and route through `references/diagnostics/hadith-authentication-epistemology.md`
- `What is withheld and why` when register-hold, semantic gate, or stop governance keeps a diagnosed downstream route from current deployment
- `What remains live` when live alternatives, held routes, or a boundary-reset condition must stay visible

**Current-pass activation rule**

- `Matched modules` records only the case-state-justified coordination active in the present pass.
- Diagnosed downstream content that is held by register, semantic, or stop governance remains explicit in Layer A through `What is withheld and why` / `What remains live`; it is not silently dropped, but it is also not treated as simultaneously active.
- `Next move` names one live move only. It is not a queue of later modules.
- When Stop-2 fires or a move has landed, boundary reset applies: later activation begins from a fresh V1-governed round rather than from carried-forward module state.

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
- `NS code: NS-6` + ontological burden live + generic restoration target. NS-6 ontological cases require a school-specific restoration target (`ḥudūth/khalq` distinction for the Muʿtazilī form; `kalām nafsī` doctrine for the Ashʿarī form), not a generic `bilā kayf` or generic foundationalist target.
- `NS code: NS-6` + ontological burden live + `Backbone predicates active` omits `O-1` and `C-1`. When NS-6 and the case involves divine attributes or speech, those predicates are minimum checks.

An IR with any of the above combinations has drifted.

---

## Compressed Form

For cases where a subset of fields is sufficient, the compressed form may be used:

```text
[IR - compressed]
Case: [family] | Claim: [type @ level?] | Pattern: [PF-x | none] | NS: [code] | Def: [code] | Conc: [mode] | Orient: [DO] | Gate: [routing gate] | Module: [matched] | Target: [restoration] | Next: [one move]
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
