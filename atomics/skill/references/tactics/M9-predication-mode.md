---
id: M9-predication-mode
module_class: tactic
canonical_path: skill/references/tactics/M9-predication-mode.md
contract_version: "0.3.0.0"
load_when:
  - equivocation across term occurrences
  - domain-boundary failure (empirical method on non-empirical subject)
  - univocal/equivocal/analogical predication question active
  - loaded negative-theological term operative
  - semantic-discipline-required gate active
routing_effects:
  - semantic-discipline-required
  - holds doctrinal-release pending predication clearance
emits:
  - ontological_disorder
  - what_is_withheld_and_why
blocks:
  - doctrinal-release before semantic clearing
  - yes/no answer on loaded term before sense-split
companions:
  - definition-discipline
  - do-attribute-precision
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-governed
catalogue_registered: true
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# M9 - Predication-Mode Analysis

**Type:** Meta-tactic
**Deploy when:** An argument's validity depends on a term carrying an identical sense across shifted occurrences; a question's coherence depends on a term applying to a domain where its meaning-conditions are not instantiated; an inference drawn by empirical-observational method is applied to a subject that method cannot access; the divine-attribute question of whether a term applies univocally, equivocally, or analogically is operative; or loaded negative theological terms are being used as if they were neutral.

**Operates upstream of content-level response selection.** Before deciding what to say about a subject, M9 determines whether the predication structure of the claim - and the inferential structure of any argument about it - is well-formed.

M9 is a selective recursive operator. A semantic or predicational clarification may clear the
question without licensing doctrinal sprawl in the same pass. After the predication problem is
typed, refresh the case-state. If another live burden now governs, route there explicitly. If
not, release only the smallest restorative next move.

---

## Function 1 - Equivocation Exposure

**Trigger:** An argument's inference depends on a term carrying the same sense across two or more of its occurrences, but the sense of the term shifts between them.

**Procedure**

1. Identify the equivocating term.
2. State its sense in each occurrence explicitly.
3. Show that the inference holds only if the senses are identical across all occurrences.
4. Show that they are not identical.
5. Name what follows: the conclusion does not follow.

**Terminal output:** logical invalidity.

---

## Function 2 - Category Error / Domain-Boundary Diagnosis

**Trigger:** A term whose meaning-conditions are constituted within one ontological, legal, or social domain is applied, without adjustment, to a subject in a categorically different domain where those conditions are absent or not instantiated.

**Procedure**

1. Identify the term and its home domain.
2. Enumerate the meaning-conditions that constitute the term's full sense in its home domain.
3. Show that those meaning-conditions are absent or non-instantiated in the target domain.
4. Conclude that the predication is malformed.

**Terminal output:** dissolution. The question is not yet well-formed.

---

## Function 2b - Ghayb-Boundary / Domain-of-Access Failure

**Trigger:** An inference drawn by empirical-observational method is applied to a subject that is accessible only through transmitted report, where the subject exists under conditions the empirical framework cannot model.

**Procedure**

1. Identify that the subject belongs to the ghayb.
2. Show that the inferential method being invoked operates on observable populations, processes, or phenomena.
3. Show that the subject lies outside those observables.
4. Conclude that the method has no jurisdiction over this subject.

**Terminal output:** method-jurisdiction failure.

---

## Function 3 - Analogical Predication (Divine Attribute Subcase)

**Trigger:** A term is denied of God on the grounds that it cannot apply univocally, and therefore cannot apply at all; or a term is applied to God univocally, importing creaturely mode as if the semantic core required it.

**Routing:** Load V8 and the relevant section of `sound-reason-epistemology.md`. M9 names the predication problem; V8 carries the divine-attribute restoration.

**Terminal output:** positive analogical affirmation. The term applies genuinely, with a different mode of instantiation.

---

## Function 4 - Loaded Negative Terms / Lexical-Ontological Trap

This section is the canonical owner for ambiguous negative theological terms. It governs cases built around labels such as `jism`, `arad`, `jihah`, `hayyiz`, `hadd`, `tarkib`, `murakkab`, `juz`, `parts`, `substance`, `body`, `direction`, `place`, `above`, `uluww`, `exaltedness`, `limit`, `composition`, and similar anti-attribute vocabulary.

These terms often hide both true and false meanings. The discipline here is mandatory: **semantic disaggregation before doctrinal engagement**.

### Required sequence

1. **Identify the intended meaning or meanings.**
   Ask what the speaker means by the term in this case. Do not assume the technical sense is stable.
2. **Split true from false meaning.**
   Separate the meaning that the tradition also rejects from the meaning being smuggled in against the tradition.
3. **Refuse yes/no concession on the unresolved label.**
   Do not answer "yes" or "no" to an ambiguous loaded term while its senses remain mixed.
4. **Only then route onward.**
   - Route to `do-attribute-precision.md` when the pressure is composition, dependence, or person/attribute confusion.
   - Route to V8 when the pressure is analogical predication and divine-attribute affirmation.
   - Route to `kalamic-interlocutor.md` when the term is functioning inside a school-specific ontological dispute.
   - Route to `perfection-criterion-usurpation.md` when the term is carrying an imported perfection tribunal.

### Minimal operator form

```text
You are using <term> as if it had one settled meaning.
Which meaning do you intend?
If you mean <false meaning>, that is rejected.
If you mean <smuggled technical meaning>, you still have to show why that meaning is the right tribunal here.
Until that split is made, the yes/no answer you want has not been earned.
```

### Prohibited moves

- Do not concede the label before its meanings are split.
- Do not answer the downstream doctrinal question while the term remains ambiguous.
- Do not treat creaturely technical categories as neutral tribunals.
- Do not move from "the term can be used in a bad sense" to "therefore every affirmation governed by that label is false."

### Failure tests

- If the response answers "God is not a body" or "God is not in a direction" without first clarifying what the speaker means, M9 did not govern.
- If the response accepts "composite" or "dependent" as a settled category before distinguishing kinds of composition and dependence, M9 did not govern.
- If the reply reaches V8, `do-attribute-precision.md`, or kalamic school-routing without first splitting the loaded term, the semantic gate was bypassed.

---

## Distinctions from Adjacent Tactics

**M7 - The Definition Anchor:** M7 handles explicit terminological dispute where the interlocutor is contesting a word. M9 handles structural predication failure and semantic traps even when the interlocutor does not name them as lexical disputes.

**M1 - Self-Refutation:** M1 shows that the premises undermine the objection. M9 shows that the inference or predication structure fails even if premises are locally true under different readings.

**M8 - Reductio:** M8 follows a position to absurd consequences. M9 diagnoses the structural failure before that stage.

**V8 - Bila Kayf:** V8 is the divine-attribute application. M9 is the upstream predicate and semantic-discipline layer that routes the divine-attribute subcase there.
