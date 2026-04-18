> role: diagnostic pipeline pass — detects and classifies imported premises, criteria, and tribunals
> use when: V1 Phase 2 axis classification is underway and the interlocutor's framework, criterion, or prior probability assignment is not yet examined
> do not use when: the claim is purely transmission-related with no criterion-importing element, or when the reason-category has already been established as sound (Category 1)
> output: a structured diagnostic pass with a defined output shape — not an optional reflective move
> pipeline position: runs as part of V1 Phase 2 alongside the deformation and concealment reads; its emission feeds the case-state
> ownership note: this file is the detection pass; arabic-backbone-predicates.md is the broader predicate library — FPD Steps 1-3 map specifically to C-1/C-2/C-3 and T-1 in ABP; for ordering violations (O-1/O-2/O-3) and category-conflation violations (K-1/K-2) that do not involve an imported foreign premise, use ABP directly; on confirmed usurpation, load philosophical-usurpation.md as the case family file

# Foreign-Premise Detection — Explicit Diagnostic Pass

This pass asks: what premise has been imported from outside the tradition being examined, from where, and how is it now functioning in the current engagement? The pass is not optional when the criterion-importing element is visible. It must either mark a premise as detected, mark none detected, or mark detection as uncertain — it cannot be skipped by elegant prose that glides past the upstream criterion.

The purpose is to prevent the most common structural failure: a response that addresses the visible objection while leaving the upstream criterion that is generating the objection unexamined. The objection can be dissolved and the criterion will regenerate a new objection from the same upstream position.

---

## Required Output Shape

Every run of this pass must produce one of the following outputs. The output feeds the case-state `Primary upstream issue` field and governs whether V2, V3, or M1 is required before content engagement.

```text
[Foreign Premise Detection]
- Premise status: <detected | none-detected | uncertain>
- Premise (if detected): <one sentence statement of the imported claim>
- Source tradition: <scientism | narrow evidentialism | historical-critical methodology | Aristotelian metaphysics | secular liberal autonomy | Mu'tazili rationalism | other: specify>
- Functional role in this case: <criterion | tribunal | prior probability assignment | definitional constraint | background assumption>
- Upstream position: <is this premise operating above or below the level of the visible objection?>
- Route consequence: <what must happen before content engagement>
- Prohibited move: <what response would grant the premise the chair>
```

If `Premise status: none-detected`, fill only the first two fields and proceed. If `uncertain`, fill through `Upstream position` and mark the decisive missing differentiator.

---

## Pass Execution Sequence

### Step 1 — Identify the Tribunal

Ask: what standard is being applied to the religious position? Not "what objection is being made?" but "what would count as a satisfying answer, and who set that standard?"

Common tribunal types:
- **Empirical verifiability:** Only claims testable by scientific method are legitimate knowledge claims. Religious claims must pass this test or are meaningless / merely subjective.
- **Historical-critical neutrality:** Scripture, revelation, and religious testimony must be evaluated using the same methods applied to ancient documents generally, with naturalistic priors. Any appeal to the tradition's own authentication criteria is question-begging.
- **Pure rational necessity:** Only what can be established by discursive argument from self-evident premises counts as knowledge. Fiṭrī recognition and tawātur-based knowledge are illegitimate without prior rational demonstration.
- **Liberal autonomy:** Individual rational consent is the ultimate legitimating criterion for any belief system. Authority, tradition, and community are obstacles to this, not epistemic inputs.
- **Aristotelian/neo-Platonic theism:** The God of revelation must be the God of the philosophers — simple, unmoved, non-personal, non-acting in time. The God who speaks, commands, and responds is less than the highest philosophical conception.

### Step 2 — Identify the Source Tradition

Where did this criterion come from? Naming the source tradition does two things: it shows the interlocutor that the criterion has a specific historical origin (not eternal philosophical necessity), and it allows the practitioner to know which family of responses addresses its specific failure modes.

### Step 3 — Identify the Functional Role

How is the premise currently functioning? The function determines the intervention:

| Functional role | What it does | V2 move required |
|----------------|--------------|-----------------|
| **Criterion** | Sets the bar evidence must clear | Show the criterion is not self-grounding; the bar itself needs justification |
| **Tribunal** | Acts as the upstream authority deciding what the tradition must answer to | Name the tribunal; show it has no special claim to the chair |
| **Prior probability assignment** | Sets a prior so low that evidence cannot overcome it | Surface the prior; show it is a philosophical choice, not a neutral starting point |
| **Definitional constraint** | Defines terms (God, reason, knowledge) in a way that makes religious claims false by definition | Expose the stipulation; insist on the distinction between definitional exclusion and discovery |
| **Background assumption** | Operates below explicit commitment as "common sense" | V2 + V7: name and externalize the assumption; make it visible as a choice |

### Step 4 — Determine Upstream Position

Is the premise operating above the visible objection? If the interlocutor's objection is downstream of the premise — if dissolving the objection will produce a new objection from the same upstream position — then the premise is upstream. Addressing the visible objection without addressing the premise wastes both parties' time. The premise regenerates.

Signal: if the interlocutor has shifted DO families (evil → evolution → hiddenness → authority) while maintaining the same underlying criterion, the premise is upstream.

### Step 5 — Route Consequence and Prohibited Move

Every detected premise specifies:
- **What must happen before content:** V2 must be run to loosen the framework; M1 applied to the criterion itself; V3 to dissolve any regress the criterion generates; the premise named as one position among alternatives.
- **What is prohibited:** Accepting the premise's terms; responding as if the criterion is legitimate and the only question is whether the religious position meets it; producing a "defense" that treats the foreign tribunal as the appropriate judge.

---

## Adversarial Near-Misses

**Near-miss 1 — Sophisticated shubhah covering upstream criterion:** An interlocutor presents a detailed philosophical objection (e.g., the problem of divine hiddenness with explicit premises and literature citations). The response routes to DO-1 and engages the philosophical apparatus. But the real governing structure is a prior-probability assignment — the interlocutor's prior for theism is set so low that no hiddenness argument could be the real driver; the hiddenness argument is the visible objection downstream of the prior. Correct detection: run Step 3 (prior probability assignment?) before loading DO-1.

**Near-miss 2 — Historical-critical methodology presented as neutral:** An interlocutor challenges the reliability of hadith transmission using historical-critical methodology and assumes the methodology is the neutral standard. The response defends specific hadith against the methodology's criteria. But the methodology itself is not neutral — it imports naturalistic priors and assumes that the same methods apply to all ancient documents regardless of their transmission architecture. Correct detection: identify the methodological framework as the foreign premise before engaging the specific hadith question.

**Near-miss 3 — Philosophical concept of God as the default:** An interlocutor argues that the God of revelation (who speaks, commands, gets "angry," responds to prayer) is anthropomorphic and philosophically primitive compared to the God of the philosophers (simple, unmoved, atemporal). The response defends divine attribute language defensively. But the premise that philosophical simplicity is the highest conception of God is itself the foreign import — the God of revelation is not required to conform to Aristotelian or neo-Platonic metaphysical categories. Correct detection: name the Aristotelian/neo-Platonic theism as the competing position, not the neutral standard against which revelation must be measured.

---

## Integration with V1 Phase 2

This pass runs in V1 Phase 2 (axis classification). Its output updates the case-state as follows:

- If `Premise status: detected` and the premise is functioning as criterion or tribunal: `Primary upstream issue` is the foreign premise. V2 is required before any content module.
- If `Premise status: detected` and the premise is a background assumption: add to the `Primary deformation` as `i'tiqadat-mawrutha` (Category 4 in reason-disambiguation.md) and route V2 + V7.
- If `Premise status: none-detected`: proceed with deformation and concealment reads as primary axis classification.
- If `Premise status: uncertain`: mark `Confidence: provisional` in the case-state and name the decisive missing differentiator.

**Connection:** This pass produces the upstream issue that V2 addresses. V2 is the intervention; this pass is the detection that triggers it. They are not interchangeable — the pass identifies whether and what kind of foreign premise is present; V2 removes it. Without the pass, V2 risks being applied to cases that do not need it (forced fit) or being skipped in cases that do (diagnosis collapse).
