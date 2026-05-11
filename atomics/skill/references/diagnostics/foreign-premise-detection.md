---
id: foreign-premise-detection
module_class: governance
canonical_path: skill/references/diagnostics/foreign-premise-detection.md
contract_version: "0.3.2.0"
load_when:
  - V1 Phase 2 axis classification; interlocutor's framework, criterion, or prior probability not yet examined
emits:
  - upstream_findings
catalogue_registered: false
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# Foreign-Premise Detection - Explicit Diagnostic Pass

This pass asks: what premise has been imported from outside the tradition being examined, from where, and how is it now functioning in the current engagement? The pass is not optional when the criterion-importing element is visible.

Its purpose is to prevent the most common structural failure: a response that addresses the visible objection while leaving the upstream criterion that is generating the objection unexamined.

Category 1 does not waive this pass if a criterion-importing element is visible. Sound reason
at the faculty level can still be presented through an imported tribunal at the case level.

---

## Layer B Activation Floor

When FPD is structurally live inside a released burden, naming "foreign premise" is not
execution. Layer B must show:

1. why the imported criterion, tribunal, source-worldview, or authority-order is governing
   the present burden;
2. the target it pressures: the exact criterion, prior, definitional constraint, or
   authority-order inversion;
3. the operation performed: expose its source, function, upstream position, and jurisdiction;
4. the result/state change: the criterion is refused, demoted, held, or handed to the next
   owner such as V2/M1/M8/M9;
5. how that result contributes to `Land(B)` so downstream content no longer answers inside
   the imported court.

If identity, school, ideology, or worldview language is present, FPD may use it only as
source-status evidence for the operative criterion. It must not treat the label itself as
proof of motive, culpability, or claim failure.

---

## Required Output Shape

Render-mode scope: this shape is an internal pass result and may be visible only in `:dsl`,
`:audit`, pass-review, or diagnostic trace. It is not a default output template; default prose
may name the imported criterion compactly when it governs the answer.

```text
[Foreign Premise Detection]
- Premise status: <detected | none-detected | uncertain>
- Premise (if detected): <one sentence statement of the imported claim>
- Premise inventory (if multiple): <numbered premise-by-premise list; do not collapse into one generic "self as criterion" claim>
- Source tradition: <scientism | narrow evidentialism | historical-critical methodology | Aristotelian metaphysics | secular liberal autonomy | Mu'tazili rationalism | other: specify>
- Functional role in this case: <criterion | tribunal | prior probability assignment | definitional constraint | background assumption>
- Upstream position: <is this premise operating above or below the level of the visible objection?>
- Route consequence: <what must happen before content engagement>
- Prohibited move: <what response would grant the premise the chair>
```

If `Premise status: none-detected`, fill only the first two fields and proceed. If `uncertain`, fill through `Upstream position` and name the decisive missing differentiator.

When the input contains multiple imported criteria or hidden premises, the pass must remain
premise-by-premise enough to govern downstream release. A single summary such as "the self is
made the criterion" may be true, but it is insufficient when different premises route to
different gates.

For secular-humanist moral protest / hiddenness / hell / worship-worthiness cases, the
minimum premise inventory normally includes:
1. Non-belief alone is insufficient ground for punishment.
2. God is morally obligated to convince every person in the manner the speaker accepts.
3. Secular-liberal moral intuitions are binding over divine action.
4. Eternal punishment is necessarily disproportionate to temporal non-belief.
5. "Worthy of worship" is being judged by an imported criterion rather than by lordship,
   truth, beneficence, justice, mercy, and right of command.

The route consequence is not to dump doctrine after naming this list. Clear the criterion,
then refresh state, then release only the next bounded doctrinal correction that remains live.
After FPD/M1 clears an imported criterion, the post-render gate must choose STOP,
RECURSE, HOLD, or PARTIAL. Do not automatically expand into hiddenness, hell,
accountability, mercy, consequence tracing, pastoral synthesis, and source lists merely
because those topics were detected downstream. Each downstream item needs renewed
eligibility from refreshed state.

---

## Pass Execution Sequence

### Step 1 - Identify the Tribunal

Ask: what standard is being applied to the religious position? Not "what objection is being made?" but "what would count as a satisfying answer, and who set that standard?"

External-criterion disclosure probe:

```text
What standard is being used to declare the revelation irrational, immoral, impossible,
inauthentic, or lower-order: sound reason, a revealed criterion, a school tradition,
modern moral intuition, Vedic reformism, historical-critical neutrality, rabbinic or
canon closure, charismatic authority, or social identity pressure?
```

Identity-linked pressure may be diagnostically relevant here as a modal/stabilizing node:
community belonging, self-narrative, public affiliation, or moral vocabulary may help explain
why a criterion is defended or costly to abandon. But identity alone is not the tribunal and does
not prove motive, deformation, culpability, or primary load-bearing status. Treat the source-status
as anchored, inference, or speculative/held before making it part of the foreign-premise read.

Common tribunal types:

- empirical verifiability
- historical-critical neutrality
- pure rational necessity
- liberal autonomy
- Aristotelian / neo-Platonic theism
- closed-canon or rabbinic closure used as veto over later divine speech
- Vedic-reformist "reason/common sense" used as tribunal over Qurʾān or prophecy
- kashf, shaykh, or tariqah authority used as jurisdiction over revelation

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

**Near-miss 1 - sophisticated shubhah covering upstream prior.**
The visible objection looks content-level, but the real driver is the prior probability assignment upstream of it.

**Near-miss 2 - historical-critical methodology presented as neutral.**
The response is tempted to defend specific reports while leaving the imported method unchallenged.

**Near-miss 3 - philosophical concept of God as default.**
The visible objection is anthropomorphism or imperfection, but the real issue is the imported tribunal.

**Near-miss 4 - validation inversion disguised as respect for reason.**
The speaker says reason merely "checks" revelation, but the actual structure is that revelation has no standing until reason has ruled. This is tribunal installation, not neutral review.

**Near-miss 4b - verifier-veto disguised as responsible authentication.**
The speaker grants that reason validates revelation or the Messenger, but keeps an indefinite
veto over every report without naming a local authenticity, semantic, or proof-strength problem.
Record `verifier-veto` with `tribunal-installation`; route P3/V2 before content.

**Near-miss 5 - tradition label hiding tribunal function.**
The surface looks like a Jewish, Hindu, Sufi, Buddhist, or moral topic, but the active
node is a criterion or authority order. Do not route by tradition label. Classify
whether the live burden is closed-canon veto, external criterion as tribunal,
kashf-as-jurisdiction, nondual category-set, identity-continuity pressure, or
source-use discipline.

**Near-miss 6 - source material invites citation dumping.**
A dossier or source trail is available, but the live structural burden has not been
typed. Do not list arguments, prooftexts, or citations until the premise status,
source tradition, functional role, and upstream position have been identified.

---

## Integration with V1 Phase 2

This pass runs in V1 Phase 2. Its output updates case-state and IR as follows:

- If `Premise status: detected` and the premise is functioning as criterion or tribunal: `Primary upstream issue` is the foreign premise. V2 is required before content.
- If `Premise status: detected` and the premise is a background assumption: add it to the deformation read as inherited framework and route V2.
- If `Premise status: detected` and validation inversion is present: surface `tribunal-installation` and, where appropriate, `transmission-demotion` in `Upstream findings`.
- If `Premise status: none-detected`: proceed with deformation and concealment reads as primary.
- If `Premise status: uncertain`: mark confidence as provisional and name the decisive missing differentiator.

This pass is the detection layer. V2 is the intervention it triggers. They are not interchangeable.

## Coverage Verification

- Failure condition: If the visible objection is answered while an imported criterion or tribunal remains unexamined upstream, the pass failed.
- IR-visible consequence: Emit the Foreign Premise Detection block, add upstream findings such as `criterion-import`, `tribunal-installation`, or `transmission-demotion`, and set the route consequence before content engagement.
- Minimal pair: Criterion import sets the bar; tribunal installation gives that bar jurisdiction; transmission demotion makes revelation derivative after rational vetting.
- Hold/release rule: Hold content that would answer inside the imported court until the source, function, and jurisdiction of the premise have been named and refused where necessary.
- Anti-pattern guard: Do not confuse this detection pass with V2; detection identifies the premise, V2 performs the restorative intervention.
- Background-material guard: Do not treat available background material as permission for argument-bank or citation-dump response. Use such material only to identify the structural premise and route consequence.
