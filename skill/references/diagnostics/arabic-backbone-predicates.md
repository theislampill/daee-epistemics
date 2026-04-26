---
id: arabic-backbone-predicates
module_class: governance
canonical_path: skill/references/diagnostics/arabic-backbone-predicates.md
contract_version: "0.2.3.0"
load_when:
  - V1 Phase 2; criterion-importing, tribunal-installation, epistemic-ordering, or transmission-conflation element visible
catalogue_registered: false
---

# Arabic-Backbone Predicates - Operational Checks from the Tradition

These predicates distill the tradition's core epistemic commitments into typed checks. Each predicate is either true, false, or unknown, and each carries a route consequence when true.

---

## Group 1 - Criterion Predicates

### Predicate C-1: Smuggled Criterion

**Check:** Has a criterion been imported as neutral reason when it is not?

**Route consequence:** V2 before content. The criterion is named, externalized, and shown to be non-self-grounding.

**Prohibited move:** Accepting the criterion as the legitimate bar and attempting to satisfy it.

### Predicate C-2: Consistent Application Check

**Check:** Is the criterion being applied to religious claims that the interlocutor does not apply to their own foundational commitments of equivalent epistemic status?

**Route consequence:** M1 against the criterion itself.

### Predicate C-3: Criterion Self-Grounding Check

**Check:** Can the criterion establish its own truth by the standards it recommends?

**Route consequence:** V3 against the criterion's own justification.

---

## Group 2 - Tribunal Predicates

### Predicate T-1: Counterfeit Tribunal

**Check:** Is a philosophical or academic system currently functioning as the upstream authority that revelation must satisfy before it is accepted?

**Route consequence:** Name the tribunal explicitly and refuse its jurisdiction before defending content within it.

### Predicate T-2: Prophetic Discourse Subjected to Later Categories

**Check:** Is prophetic discourse being treated as if it were accountable to later kalamic or philosophical categories before it can carry weight?

**Route consequence:** Restore the order. Prophetic address is primary; later kalamic demonstration is remedial and secondary.

### Predicate T-3: Later Foundation Mistaken for Pure Foundation

**Check:** Has a later technical philosophical or theological foundation been presented as if it were the religion's own primary foundation?

**Route consequence:** Distinguish the religion's foundations from later frameworks layered onto them.

---

## Group 3 - Ordering Predicates

### Predicate O-1: Reason-Over-Transmission Inversion

**Check:** Is reason being treated as the validating tribunal that grants transmission standing, instead of as a faculty that remains sound only in right order with revelation?

**True when:** The case does more than import a criterion. It structurally demotes transmission by making revelation epistemically derivative, confirmatory, or admissible only after reason has already ruled on its content or legitimacy.

**Route consequence:** Surface `tribunal-installation` and, where applicable, `transmission-demotion` in the case-state or IR. Hold content until the inversion is named and refused. The correction is not merely "reason and revelation agree"; it is that revelation is not a downstream branch licensed by reason's court.

### Predicate O-2: Fiṭrah Recognition Demoted Below Its Epistemic Grade

**Check:** Is the `fiṭrah` being treated as probable or sub-epistemic rather than as non-inferential knowledge when sound?

**Route consequence:** V9.

### Predicate O-3: Sign Converted to Premise

**Check:** Has an ayah/sign been converted into a logical premise rather than presented as a sign directing attention?

**Route consequence:** V5.

---

## Group 4 - Category Predicates

### Predicate K-1: Unlike Transmission Systems Conflated

**Check:** Are the transmission systems of different traditions being treated as equivalent in kind?

**Route consequence:** V10 branch selection and transmission-architecture distinction.

### Predicate K-2: Lexical, Technical, and Shar'i Levels Collapsed

**Check:** Has a term being used in one level - lexical, technical, ontological, or shar'i - been received or deployed as if it already carried another level?

**Route consequence:** Re-state the level of the claim explicitly.

---

## Predicate Emission Format

```text
[Backbone Predicates]
- C-1 (smuggled criterion): true / false / unknown
- C-2 (consistent application): true / false / unknown
- C-3 (self-grounding): true / false / unknown
- T-1 (counterfeit tribunal): true / false / unknown
- T-2 (prophetic discourse subjected to later categories): true / false / unknown
- T-3 (later foundation mistaken for pure foundation): true / false / unknown
- O-1 (reason-over-transmission inversion): true / false / unknown
- O-2 (fiṭrī recognition demoted): true / false / unknown
- O-3 (sign converted to premise): true / false / unknown
- K-1 (unlike transmission systems conflated): true / false / unknown
- K-2 (lexical / technical / shar'i levels collapsed): true / false / unknown
- Active predicates: [list true ones]
- Route consequences: [list what each active predicate requires]
```

Compression rule: run only the checks relevant to the live case. If no backbone predicate fires, emit `none active`.

---

## Trigger Mapping - Minimum Checks by Case Surface

| Case surface | Check minimally |
|---|---|
| NS-1 (Naturalist) | C-1, C-2, C-3 |
| NS-6 - epistemological burden | T-2, T-3 |
| NS-6 - ontological burden (divine attributes or speech live) | T-2, T-3, O-1, C-1 |
| NS-9 (Historical-Critical Skeptic) | K-1, C-1 |
| NS-10 (Maturidi Evidentialist) | T-2, O-2 |
| DO-5 (Transcendence and language) | O-1, K-2; if the objection is phrased through loaded negative terms, run M9 before doctrinal release |
| DO-6 (Attribute coherence) | C-1, O-1; if body/direction/composition/limit vocabulary is doing the work, run M9 before V8 or attribute-precision fixtures |
| DO-13 (Philosopher's God vs. God of revelation) | T-1, T-3, O-1, C-1 |
| DO-11/12 (Trinity pressure) | K-1, C-1 |
| RT-1/RT-3 | K-1 |
| Any case where "God must be X" appears | T-1, T-3, C-1 |
| Any case where fiṭrī recognition is dismissed | O-2, O-3 |
| Any case where kalamic proof is demanded | T-2, O-3 |
| Any case built on loaded negative theological terms | M9 semantic split before doctrinal content; add K-2 only when lexical, technical, ontological, or shar'i levels are being collapsed; add definition-discipline.md when hidden technical narrowing is manufacturing the objection |

---

## Failure Test

This file has not been applied if:

- criterion-importing, tribunal-installation, or ordering-violation elements were visible in the input, but `none active` was emitted without checking the relevant predicates from the trigger mapping
- a backbone predicate fired but no route consequence was recorded
- the compression rule was invoked to avoid minimum checks named in the trigger mapping
