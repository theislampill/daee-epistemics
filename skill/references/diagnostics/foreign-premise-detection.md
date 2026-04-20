> role: diagnostic pipeline pass - detects and classifies imported premises, criteria, and tribunals
> use when: V1 Phase 2 axis classification is underway and the interlocutor's framework, criterion, or prior probability assignment is not yet examined
> do not use when: the claim is purely transmission-related with no criterion-importing element
> output: a structured diagnostic pass with a defined output shape
> pipeline position: runs as part of V1 Phase 2 alongside the deformation and concealment reads
> ownership note: this file is the detection pass; `arabic-backbone-predicates.md` is the broader predicate library

# Foreign-Premise Detection - Explicit Diagnostic Pass

This pass asks: what premise has been imported from outside the tradition being examined, from where, and how is it now functioning in the current engagement? The pass is not optional when the criterion-importing element is visible.

Its purpose is to prevent the most common structural failure: a response that addresses the visible objection while leaving the upstream criterion that is generating the objection unexamined.

Category 1 does not waive this pass if a criterion-importing element is visible. Sound reason
at the faculty level can still be presented through an imported tribunal at the case level.

---

## Required Output Shape

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

If `Premise status: none-detected`, fill only the first two fields and proceed. If `uncertain`, fill through `Upstream position` and name the decisive missing differentiator.

---

## Pass Execution Sequence

### Step 1 - Identify the Tribunal

Ask: what standard is being applied to the religious position? Not "what objection is being made?" but "what would count as a satisfying answer, and who set that standard?"

Common tribunal types:

- empirical verifiability
- historical-critical neutrality
- pure rational necessity
- liberal autonomy
- Aristotelian / neo-Platonic theism

### Step 2 - Identify the Source Tradition

Where did this criterion come from? Naming the source tradition shows the criterion has a specific historical origin rather than neutral self-evidence.

### Step 3 - Identify the Functional Role

How is the premise currently functioning?

| Functional role | What it does | V2 move required |
|----------------|--------------|------------------|
| `criterion` | Sets the bar evidence must clear | Show the criterion is not self-grounding |
| `tribunal` | Acts as upstream authority deciding what the tradition must answer to | Name the tribunal and question its jurisdiction |
| `prior probability assignment` | Sets a prior so low that evidence cannot overcome it | Surface the prior and show it is a philosophical choice |
| `definitional constraint` | Defines terms so the religious claim is false by definition | Expose the stipulation |
| `background assumption` | Operates below explicit commitment as common sense | Externalize it as a choice |

### Step 4 - Determine Upstream Position

Is the premise operating above the visible objection? If dissolving the visible objection will simply regenerate a new objection from the same premise, then the premise is upstream.

### Step 5 - Route Consequence and Prohibited Move

Every detected premise specifies:

- what must happen before content
- what is prohibited

Typical consequence: V2 must be run to loosen the framework before content is released.

### Source-Native Foundations vs. Constructed Foundations

When the imported criterion presents itself as "the principles" that revelation must
obey, ask whether those principles are source-native or constructed upstream of the
source. A constructed foundation may use religious vocabulary while still functioning as
a foreign tribunal if it decides in advance what transmitted discourse may mean.

Route consequence: mark `tribunal-installation` rather than treating the case as a
mere disagreement over conclusions. The next move is to restore authority order before
answering the downstream doctrinal issue.

---

## Validation Inversion / Transmission Demotion Check

This subsection is mandatory whenever the case includes language like "reason first proves revelation," "reason validates transmission and therefore outranks it," "transmission only counts after rational vetting of its content," or any equivalent framing.

### What to detect

Distinguish three related but non-identical findings:

1. **Criterion import present**
   Reason or rational necessity is being used as the bar revelation must clear.
2. **Tribunal installation present**
   Reason is not merely one tool among others; it is installed as the court before which transmission must justify itself.
3. **Transmission demotion / inversion present**
   Transmission is treated as derivative, confirmatory, or epistemically downstream of reason in a way that removes its native standing as source.

### Minimal discriminator

- **Imported criterion only:** "Your text must satisfy my rational standard."
- **Tribunal installation:** "Reason decides what revelation is allowed to say."
- **Transmission demotion:** "Transmission only has standing after reason has already validated its content or category."

### Route consequence

When tribunal installation or transmission demotion is present:

- mark `Primary upstream issue` in tribunal language, not merely objection language
- add `tribunal-installation` and, when appropriate, `transmission-demotion` to `Upstream findings`
- connect the case to `O-1` in `arabic-backbone-predicates.md`
- hold doctrinal content until the inversion is named and refused

### Prohibited move

Do not answer as if revelation were merely a downstream confirmation of what reason already owns. That concedes the inversion before it is examined.

---

## Adversarial Near-Misses

**Near-miss 1 - sophisticated shubha covering upstream prior.**
The visible objection looks content-level, but the real driver is the prior probability assignment upstream of it.

**Near-miss 2 - historical-critical methodology presented as neutral.**
The response is tempted to defend specific reports while leaving the imported method unchallenged.

**Near-miss 3 - philosophical concept of God as default.**
The visible objection is anthropomorphism or imperfection, but the real issue is the imported tribunal.

**Near-miss 4 - validation inversion disguised as respect for reason.**
The speaker says reason merely "checks" revelation, but the actual structure is that revelation has no standing until reason has ruled. This is tribunal installation, not neutral review.

---

## Integration with V1 Phase 2

This pass runs in V1 Phase 2. Its output updates case-state and IR as follows:

- If `Premise status: detected` and the premise is functioning as criterion or tribunal: `Primary upstream issue` is the foreign premise. V2 is required before content.
- If `Premise status: detected` and the premise is a background assumption: add it to the deformation read as inherited framework and route V2.
- If `Premise status: detected` and validation inversion is present: surface `tribunal-installation` and, where appropriate, `transmission-demotion` in `Upstream findings`.
- If `Premise status: none-detected`: proceed with deformation and concealment reads as primary.
- If `Premise status: uncertain`: mark confidence as provisional and name the decisive missing differentiator.

This pass is the detection layer. V2 is the intervention it triggers. They are not interchangeable.
