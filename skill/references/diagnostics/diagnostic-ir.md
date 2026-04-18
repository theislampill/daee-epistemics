> role: dispatch gate and typed diagnostic intermediate representation — the constrained layer that module dispatch must pass through before any content module is loaded
> use when: any substantive engagement requiring routing; the IR is not optional for these cases — it is the gate
> do not use when: the task is a narrow conversational sub-answer with no case classification required
> output: a typed diagnostic state that gates module dispatch; also serves as the auditable record of the routing decision and architectural alignment

# Diagnostic IR — Dispatch Gate and Typed Intermediate Representation

This file defines the complete typed state that must be formed before any content module is dispatched. It sits between the workflow layer (routing procedure) and the metaphysical-architecture layer (what is being restored). Its purpose is twofold: (1) to gate module dispatch — dispatch is blocked until the mandatory minimum fields are populated and consistency checks pass; (2) to make routing auditable independently of prose quality — a response whose prose is eloquent but whose IR is inconsistent or incomplete has drifted, and the drift is detectable.

**The IR is not a retrospective record.** Writing the IR after the response is cosmetic compliance — the IR's function is to govern dispatch, not to document it after the fact. If the IR cannot be formed because mandatory fields cannot be populated, the correct action is Stop-4 (Underdetermined-Case Stop), not a response with a post-hoc IR.

The IR composes fields from several sources:
- Case-state fields (from `case-state-schema.md`)
- Reason-category fields (from `reason-disambiguation.md`)
- Backbone predicate emissions (from `arabic-backbone-predicates.md`)
- Foreign-premise detection (from `foreign-premise-detection.md`)
- Philosophical-usurpation fields (from `philosophical-usurpation.md` when active)
- Architectural layer disruption (from `metaphysical-architecture.md`)
- P7 stop status (from `P7-restoration-stops.md`)
- Routing-precedence state (from `routing-precedence.md`)

---

## Gate Protocol — Required Before Module Dispatch

Before any content module is dispatched, the following checks must pass in order. If any check fails, dispatch is blocked; the blocking condition is named explicitly rather than silently resolved.

**Gate Check 1 — Mandatory minimum fields populated.**
All fields in the mandatory minimum (see §Field Rules below) must be populated. Fields that cannot be populated because the basis is too thin route to Stop-4, not to a partial IR.

**Gate Check 2 — Consistency rules pass.**
None of the invalid combinations (see §Field Rules below) may be present. An IR with an invalid combination is a misread — re-run Phase 2 before dispatching.

**Gate Check 3 — Routing-precedence suppression rules applied.**
Apply `routing-precedence.md` Suppression Rules S-1 through S-5. If any suppression rule fires, the routing gate is blocked for the operation that rule suppresses, regardless of how strong the NS/deformation read is. Note the active suppression rule in the `P7 stops active` and `Routing gate` fields.

**Gate Check 4 — P7 stops checked.**
Each P7 stop, when triggered, blocks the corresponding content operation. Check all five stops before dispatch. Record active stops in the IR. An active P7 stop is a gate block for its governed operation — not an advisory.

**Gate Check 5 — Architectural integrity check.**
The `Restoration target` field must name a specific epistemic layer (fiṭrah / sound reason / authentic transmission / inferential argument) or ontological distinction (creator-creation / transcendence-immanence / prophetic authority) from `metaphysical-architecture.md`. A restoration target stated as "correct the interlocutor's argument" or "demonstrate X" has not been grounded in the architecture. Re-state it in terms of what faculty, ordering, or distinction is being restored in the interlocutor's noetic structure. Also check that no `kernel-thesis.md` violation signature is present in the response being planned.

**Gate Check 6 — Route cleared for content.**
After Checks 1-5 pass: confirm the concealment × orientation matrix (in `case-state-schema.md`) shows content is deployable now. If register-hold applies, the matched content module is held — not dispatched.

Only after all six checks pass does module dispatch proceed.

---

## Full IR Schema

```text
[Diagnostic IR]

--- Workflow Layer ---
Case family:
Claim-type:                          # logical | metaphysical | moral | historical | transmission | phenomenological | authority
NS code:                             # NS-1 through NS-12, or provisional
Deformation:                         # primary [| secondary], in intervention order
Concealment mode:                    # irad | juhud | inkar | istikbar | nifaq | mode-? | compound
DO-orient:                           # truth-seek | identity-perf | autotelic | zann-mode | mixed
RT marker (if active):               # RT-1 | RT-2 | RT-3 | RT-4 | none
Read status:                         # dominant | distributed | underdetermined
Confidence:                          # strong | provisional | low
P7 stops active:                     # Stop-1 | Stop-2 | Stop-3 | Stop-4 | Stop-5 | none
Routing gate:                        # open | V2-required | deformation-first | register-hold | stop-condition
Matched modules:                     # smallest matched subset only
Prohibited moves:                    # list any PM from routing-precedence or do-attribute-precision

--- Architectural Layer ---
Reason-category:                     # 1 (sound) | 2 (corrupted) | 3 (pseudo-neutral) | 4 (inherited)
Backbone predicates active:          # list true predicates from arabic-backbone-predicates.md
Foreign premise:                     # detected [premise, source, functional role] | none-detected | uncertain
Philosophical usurpation:           # type [A | B | C | D] + active telltale features | none
Architectural layer disrupted:       # fiṭrah | sound-reason | authentic-transmission | inferential-route | transcendence-immanence | prophetic-authority | none
Ontological disorder:                # category-mistake | illicit-analogy | equivocal-predication | composition-panic | person-multiplicity-conflation | perfect-being-usurpation | none
Restoration target:                  # what noetic faculty, epistemic ordering, or ontological distinction is being cleared or re-established

--- Output Governance ---
Source basis:                        # [anchored] | [synthesis] | [inference] | [speculative] — per claim
Inference boundary active:           # yes | no
Output shape:                        # content | relational | maieutic | invitational | single-response | held-pending
Next move:                           # one specific action the response takes next
What is withheld and why:            # if anything is held back
What remains live:                   # open differentiators, unresolved axes, or questions the next exchange must answer
```

---

## Field Rules

**Compression rule:** The IR is not a checklist to be filled performatively. Populate only fields with operative content. A field left blank is not a failure — it is a correct report that the dimension is not active or not yet determined. Populating every field with null values is a violation of the compression rule and produces transparency theater.

**Mandatory minimum:** For any substantive response claiming to have done V1, the following fields must be populated:
- Case family
- Claim-type
- Deformation (even if `shubha` or `unknown`)
- Concealment mode (even if `mode-?`)
- DO-orient
- Reason-category
- Routing gate
- Matched modules
- Restoration target
- Next move

If these fields cannot be populated because the basis is too thin, the correct output is Stop-4 (Underdetermined-Case Stop) plus the specific missing differentiator — not a partial IR that appears to have governed the response.

**Consistency rule:** The fields must be internally consistent. The following inconsistencies are invalid:
- `Read status: underdetermined` + `Confidence: strong`
- `Concealment: juhud` + `Output shape: content`
- `P7 Stop-1 active` + `Output shape: content`
- `Routing gate: V2-required` + `Matched modules: [any content module]`
- `DO-orient: identity-perf` + `Matched modules: [any doctrinal case file]`
- `Reason-category: 3 or 4` + `Routing gate: open`
- `NS code: NS-6` + `Restoration target: [generic foundationalist restriction or generic wujūb al-naẓar]` + `Architectural layer disrupted: transcendence-immanence` — invalid because NS-6 ontological cases require a school-specific restoration target (Muʿtazilī: ḥudūth/khalq distinction; Ashʿarī: kalām nafsī doctrine), not a generic bilā kayf or foundationalist-restriction target. If the architectural layer is disrupted at transcendence-immanence and the NS code is NS-6, the restoration target must name the school-specific ontological error, and `Matched modules` must include §6.2 of `sound-reason-epistemology.md` and V8.
- `NS code: NS-6` + `Restoration target: [any ontological target]` + `Backbone predicates active: [T-2, T-3 only]` — invalid when ontological burden is live. When NS-6 and the case involves divine attributes or speech, O-1 and C-1 must be checked as minimum (see `arabic-backbone-predicates.md` NS-6 ontological row); a backbone-predicate emission that omits them when the ontological dimension is active has not completed the mandatory check.

An IR with any of the above combinations has a workflow-architecture inconsistency and the response it governs has drifted.

---

## Compressed Form (When Full IR Is Not Warranted)

For cases where a subset of fields is sufficient — a single clear read, a narrow objection, a well-established register — the compressed form may be used:

```text
[IR — compressed]
Case: [family] | Claim: [type] | NS: [code] | Def: [code] | Conc: [mode] | Orient: [DO] | Gate: [routing gate] | Module: [matched] | Target: [restoration] | Next: [one move]
```

The compressed form is acceptable when the full IR's additional fields would all be empty or default. It is not acceptable when architectural-layer fields are active (reason-category ≠ 1, backbone predicates active, foreign premise detected, philosophical usurpation confirmed) — those cases require the full form.

---

## How the IR Prevents Cosmetic Compliance

Cosmetic compliance occurs when the practitioner acknowledges the workflow while the actual output imports the wrong framework. Specific failure modes:

**Cosmetic V1 compliance:** The response states that V1 was run and assigns an NS code, but the case-state deformation is `shubha` when the actual pattern signals `hawa`, and the matched modules are doctrinal content modules. The IR catches this because `Deformation: shubha` + `Matched modules: [content]` is valid, but `Routing gate: open` with `DO-orient: identity-perf` is invalid — the inconsistency is visible in the IR without needing to read the prose.

**Cosmetic framework-clearing:** The response names V2 as a technique to be deployed, but the matched modules include content deployed into the unreconstituted filter (Cumulative Inflation anti-pattern). The IR catches this because `Routing gate: V2-required` with any content module in `Matched modules` is an invalid combination.

**Cosmetic register acknowledgment:** The response acknowledges grief as present but still outputs propositional content. The IR catches this because `P7 Stop-1 active` with `Output shape: content` is invalid.

**Architectural drift:** The response satisfies V1 and selects correct modules but the `Restoration target` is stated as "correct the interlocutor's argument" rather than as a faculty or epistemic ordering being restored. The IR catches this because the restoration target must name what is being restored in the interlocutor's noetic or epistemic structure — not what is being won in the argument.

---

## Connection to Framework Pipeline

`framework-pipeline.md` shows the structural branching of the canonical pipeline. `routing-precedence.md` specifies the decision rules at each branch point. This file (diagnostic-ir.md) is the gate and the typed state produced at the end of V1 Phase 2 — the check that must be passed before module selection occurs. The three files are the structural chart, the decision rules, and the gate/record — together they constitute the complete governance apparatus for routing decisions.

---

## Failure Tests

The following conditions indicate this file has not governed the response, even if an IR block appears:

- **IR written after the response:** The IR was composed to match a response already drafted. The IR must precede dispatch. If the IR was formed after dispatch, it is cosmetic compliance.
- **Restoration target is argumentative, not restorative:** The restoration target names what argument is being won, not what epistemic faculty or ordering is being restored. Check against `metaphysical-architecture.md` four-layer taxonomy.
- **Mandatory minimum fields are empty but IR is marked complete:** Empty fields are not populated fields. Stop-4 is the correct output when mandatory fields cannot be grounded.
- **Suppression rule is active but corresponding module was dispatched:** A firing S-rule blocks the operation it governs absolutely. If a module was dispatched while its governing suppression rule was active, Gate Check 3 was not applied.
- **Consistency rule violation present but response proceeded:** Any invalid combination in the consistency rules constitutes a workflow-architecture inconsistency. The response that follows it has drifted even if the prose is strong.
