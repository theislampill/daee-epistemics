> role: typed diagnostic intermediate representation — binds workflow layer to metaphysical-architecture layer
> use when: producing a full case-state for a substantive engagement where routing must be auditable independently of prose quality; prevents cosmetic workflow compliance from masking architectural drift
> do not use when: the task is a narrow conversational sub-answer with no case classification required
> output: a typed diagnostic state with explicit fields for all governed dimensions; serves as the auditable record of both the routing decision and the architectural alignment

# Diagnostic IR — Typed Intermediate Representation

This file defines the complete typed state that sits between the workflow layer (routing procedure) and the metaphysical-architecture layer (what is being restored). Its purpose is to make routing auditable independently of prose quality — a response whose prose is eloquent but whose IR is inconsistent or incomplete has drifted, and the drift is detectable.

The IR composes fields from several sources:
- Case-state fields (from `case-state-schema.md`)
- Reason-category fields (from `reason-disambiguation.md`)
- Backbone predicate emissions (from `arabic-backbone-predicates.md`)
- Foreign-premise detection (from `foreign-premise-detection.md`)
- Philosophical-usurpation fields (from `philosophical-usurpation.md` when active)
- Architectural layer disruption (from `metaphysical-architecture.md`)
- P7 stop status (from `P7-restoration-stops.md`)
- Routing-precedence state (from `routing-precedence.md`)

The IR does not replace these files. It is the composed output that proves they were actually consulted and their results actually governed the response — not bypassed by elegant summary.

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

`framework-pipeline.md` shows the structural branching of the canonical pipeline. `routing-precedence.md` specifies the decision rules at each branch point. This file (diagnostic-ir.md) is the output artifact that proves the pipeline was traversed correctly — the typed state produced at the end of V1 Phase 2 and the beginning of module selection, against which the response is auditable. The three files are the structural chart, the decision rules, and the output record — together they constitute the complete governance apparatus for routing decisions.
