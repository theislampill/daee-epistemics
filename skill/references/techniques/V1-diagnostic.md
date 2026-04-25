---
id: V1-diagnostic
module_class: technique
canonical_path: skill/references/techniques/V1-diagnostic.md
contract_version: "0.2.0.0"
load_when:
  - beginning any engagement before substantive content
  - interlocutor shifts register
  - upstream barrier cleared and new downstream issue exposed
routing_effects:
  - establishes case-state required before any other module loads
  - runs M5-deformation-triage as internal subroutine
emits:
  - case_family
  - ns_code
  - discourse_orientation
  - concealment_mode
  - deformation_type
  - matched_modules
blocks:
  - any tactic, technique, procedure, or case-library module before case-state is produced
companions:
  - M5-deformation-triage
  - prophetic-discourse-neutralization
  - causal-series-taxonomy
  - definition-discipline
  - proof-method-audit
  - perfection-criterion-usurpation
output_shapes:
  - pass-through
layer_constraint: layer-a-only
---

# V1 - The Diagnostic Technique

> role: entry gate for all substantive engagements
> use when: beginning any engagement, whenever the interlocutor shifts register, or whenever a move clears an upstream barrier and exposes a new downstream issue
> do not use when: the task is a narrow factual clarification with no routing consequence
> output: a composed case-state line plus the matched next module

## Role of V1 in the Skill

V1 is the entry gate. No tactic, technique, procedure, or case-library module is selected before V1 has produced a case-state. V1 does not answer the interlocutor; it produces the routing artifact that makes a matched answer possible.

## The Three Phases

### Phase 1 - Listening

Extended, non-argumentative engagement whose purpose is to map the interlocutor's actual noetic structure.

Track:

- what is held with the firmness of necessary knowledge
- what functions as the implicit doxastic rule
- what counts as evidence, warrant, and authority
- where affective weight sits
- what is conspicuously absent from the framework

### Phase 2 - Classification

Produce short codes on the main axes:

- NS code
- discourse orientation
- concealment
- deformation
- claim-type
- claim-level when a higher-order burden is visible or the full IR is being surfaced
- pattern profile when one recurring PF family is governing

Then run the mandatory passes in sequence:

1. `reason-disambiguation.md`
2. `foreign-premise-detection.md`
3. `prophetic-discourse-neutralization.md`
4. `arabic-backbone-predicates.md`

### Specialty markers to surface early

- `dalīl`, `wujūb al-naẓar`, or `taqlīd`-as-non-knowledge -> `kalamic-interlocutor.md`
- blank-slate or dual-nature `fiṭrah` language -> `fitrah-perspectives.md`
- attacks on necessary knowledge -> V9
- historical-critical, manuscript, canon, or text-history pressure -> V10 and the matched RT case
- prophetic discourse being redirected, semantically overridden, or evacuated -> `prophetic-discourse-neutralization.md`
- loaded negative theological terms (`jism`, `jihah`, `hadd`, `tarkib`, body, direction, place, limit, composition, substance) -> M9 before doctrinal release
- imported perfection / immutability / simplicity tribunal -> `perfection-criterion-usurpation.md`
- causal regress, simultaneous/successive series, circularity, or secondary-cause self-sufficiency -> `causal-series-taxonomy.md`
- public-language capture, silent redefinition, universals/particulars confusion, or mental/extra-mental confusion -> `definition-discipline.md`
- necessity/contingency proof-grammar pressure or philosophically trained proof-overreach -> `proof-method-audit.md`

### Phase 3 - Triage

Determine which instrument is the smallest matched next step, and in what order if multiple are required.

Use M5 as the deformation-triage subroutine inside V1, not as a rival opening architecture.

Compound-case sequencing rule:

- `ada` before `i'tiqadat mawrutha`
- `gharad` and `hawa` before intellectual content
- `i'tiqadat mawrutha` before evidence
- `zann` and `taqlid` in parallel where appropriate
- genuine `shubha` last

Cross-axis precedence:

- if DO-orient is non-truth-seeking, the next step is almost never a doctrinal case file
- if concealment is `irad`, argument is held until the matter has been allowed to press
- if concealment is `juhud` or `istikbar`, argument will not land
- if reason-category or foreign-premise detection makes V2 mandatory, content waits
- if semantic neutralization or a lexical-ontological trap is live, doctrinal content waits behind the semantic gate

## The Case-State Output

V1 terminates in a composed line that feeds `case-state-schema.md`:

```text
Case: <family>    Claim: <type> [@ <level>]    Pattern: <PF-X | none>    NS: NS-X [| NS-Y]    DO-orient: <code>    Concealment: <code>    RT (if applicable): <RT-X>    Deformation: <primary> [| <secondary>]    Strength: <strong | provisional | low>    Next: <smallest matched module>
```

Omit `@ <level>` only when the case is routine first-order after higher-order triggers
have been checked and found inactive.

Where legibility is needed, surface the fuller `[Case State]` block from `case-state-schema.md`.

## Critical Warning

Presenting intellectual content to someone whose governing barrier is vested interest, entrenched will, identity-performance, semantic neutralization, or a loaded lexical trap does not merely fail; it gives the barrier new material to organize around.

## Downstream Ordering Rule

Once V1 has produced the case-state and M5 has confirmed the governing deformation, run M1 or M1-P first among downstream moves whenever self-refutation is actually present.

## When to Re-Run V1

Re-run or update the case-state whenever:

- a move clears an upstream barrier and exposes a new downstream issue
- the interlocutor shifts register
- affective tone shifts significantly
- a new objection family appears
- the case becomes genuinely mixed
