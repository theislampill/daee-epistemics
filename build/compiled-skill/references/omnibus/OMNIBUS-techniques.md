<!--
GENERATED FILE.
Do not edit directly.
Canonical source lives under skill/.
Regenerate with tools/build_compiled_runtime.py.
-->

# OMNIBUS-techniques

This generated bundle is a runtime read view. Section presence does not imply active dispatch.


## SOURCE MODULE: techniques-index

<!-- SOURCE: skill/references/techniques/INDEX.md -->
<!-- MODULE_ID: techniques-index -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: skill/references/techniques/INDEX.md -->
<!-- SOURCE_SHA256: 316f880e27c64e09ddb048a1903a00d470f2dab960cf22cfdaf9b37374aaf5d2 -->

---
id: techniques-index
module_class: governance
canonical_path: skill/references/techniques/INDEX.md
contract_version: "0.2.3.0"
load_when:
  - selecting a technique after V1 case-classification
catalogue_registered: false
---

# Techniques - Index

Techniques govern a stretch of conversation. A technique is broader than a tactic and narrower than a full procedure.

## Selection Rules

- Use a technique when the case needs an architectural approach, not just a single move.
- Do not stack techniques unless each one changes the next stage of engagement.
- When in doubt, prefer the earlier clearing technique over the later sign-direction technique.
- V1 is the umbrella entrypoint for substantive cases; M5 operates inside V1 rather than beside it.
- In revelation, scripture, transmission, canon, preservation, and text-history cases, run V10 before broader doctrinal rebuttal or case-library deployment.

## Techniques

| File | Role | Use when | Do not use when | Typical pairings |
|------|------|----------|-----------------|-----------------|
| `references/techniques/V1-diagnostic.md` | Intake and triage | Beginning any substantive engagement | Never skip when the case is structurally live | M5, `noetic-reading-checklist.md` |
| `references/techniques/V2-reconstituting-reason.md` | Framework clearing | The interlocutor's conception of reason is contaminated | The issue is grief-primary or already framework-clear | E1, P3 |
| `references/techniques/V3-regress-dissolution.md` | Regress handling | The interlocutor keeps pressing justificatory regress | The real issue is causal-series classification or proof grammar rather than justificatory regress | E2, R1 |
| `references/techniques/V4-contamination-identification.md` | Contamination naming | A caricature of reason or revelation is blocking recognition | The case is already cleanly specified and needs no contamination pass | V2, V8 |
| `references/techniques/V5-directing-attention-signs.md` | Sign-direction | The framework has been cleared and signs can now be presented | The framework is still filtering everything through a prior block | R2, P1 |
| `references/techniques/V6-convergence.md` | Multi-register integration | Cross-register convergence itself is the needed point after clearing | One upstream obstruction still dominates | E3, V5 |
| `references/techniques/V7-taqlid-check.md` | Default skepticism exposure | Skepticism appears inherited rather than examined | You have not applied the symmetric check inward where needed | `symmetric-taqlid-check.md` |
| `references/techniques/V8-bila-kayf-anchor.md` | Attribute discipline | Transcendence, attributes, Trinity-adjacent language, incarnation coherence, or philosopher's-God pressure is primary | The case has already moved to testimony or revelation authority | DO-5, DO-6, DO-11 to DO-13 |
| `references/techniques/V9-necessary-knowledge-priority.md` | Necessity-over-inference control | A discursive argument contradicts universally held fiṭrī knowledge | The argument is merely unpopular or difficult, not anti-necessary | E4, DO-7, DO-9 |
| `references/techniques/V10-transmission-content-vetting.md` | Transmission and source discipline | Revelation, scripture, manuscript, canon, preservation, historical-critical, original-text, or testimony claims need separation | The issue is generic theism, grief, or attribute language rather than source-vetting | RT-1 to RT-4, P2, P5 |
| `references/techniques/V11-taqlid-transition.md` | Structured transition from `taqlīd` to `taḥqīq` | The subject has recognized their position is held by `taqlīd` and is willing to transition | The subject is still defending the `taqlīd`; V7 must precede V11 | V7, `symmetric-taqlid-check.md`, V9 |
| `references/techniques/V12-tamanuc-exhaustion.md` | Logical exhaustion of divine plurality | Any claim of divine plurality, polytheism, or multiple independent lords | The question is not about independent lordship at all | V8, DO-11, DO-13 |
| `references/techniques/heuristics.md` | Always-active analyst discipline | You need the standing operator rules and self-audit frame | Not a move to cite as if it were a tactic | All folders |

## Structural Subtype Checks

- `Mushabara fasida` is the deformation-1 subtype where one premise is doing the load-bearing work.
- If the live issue is causal-series type, circularity taxonomy, or necessity/contingency overreach, route through `causal-series-taxonomy.md` and `proof-method-audit.md` before inferential content is selected.

<!-- END_SOURCE: techniques-index -->


## SOURCE MODULE: V2-reconstituting-reason

<!-- SOURCE: skill/references/techniques/V2-reconstituting-reason.md -->
<!-- MODULE_ID: V2-reconstituting-reason -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V2-reconstituting-reason.md -->
<!-- SOURCE_SHA256: b59382e5db47b2c8c691c3b3599efd2d2d6a50f346b0812396c04b1ab73a102e -->

---
id: V2-reconstituting-reason
module_class: technique
canonical_path: skill/references/techniques/V2-reconstituting-reason.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor's conception of reason is contaminated (bidʿī ʿaqlī)
  - evidential content cannot land through the interlocutor's filter
  - reason or evidence concept implicitly restricted to empirically testable or scientism-narrowed scope
routing_effects:
  - holds first-order content pending filter identification and loosening
  - clears imported tribunal at ʿaql layer (tribunal-loosened)
emits:
  - what_is_withheld_and_why
companions:
  - V4-contamination-identification
  - V5-directing-attention-signs
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V2 — Reconstituting the Conception of Reason

**Deploy when:** Interlocutor's conception of reason is contaminated (bidʿī ʿaqlī); before any evidential content can land through the contaminated filter.

Most often deployed before any other technique. Many contemporary interlocutors operate with an inherited conception of reason — "reasoning properly" means applying the methods of natural science to all questions, or only empirically verifiable claims are meaningful. Others import the same problem through theological vocabulary: only a narrow class of necessary knowledge counts, or revelation must submit to a prior metaphysical picture presented as neutral reason. This feels like reason itself. It is a historically contingent philosophical stance that became dominant in certain intellectual traditions and is anything but self-evident.

**Three steps:**
1. *Name the framework, not the conclusion.* Ask the interlocutor to articulate what they mean by "reason," "evidence," or "rational belief." Making the implicit framework explicit creates space to examine it rather than argue within it. Often the real framework is scientism, a narrow necessary-knowledge criterion, or a philosophical picture of divine perfection that has been mistaken for reason as such.
2. *Show the framework is one position among several.* It was not always dominant, is not universal, and is not established by the methods it recommends. Scientism cannot validate itself scientifically. A self-styled "universal law" that revelation must submit to a prior rational filter still needs justification for that filter. A worldview that can only be accepted by its own standards is circular, not foundational.
3. *Propose the alternative.* ʿAql ṣarīḥ — genuine reason, operating without historically contingent distortions — is fully capable of apprehending theistic truth.

> The question is never "can you believe in God despite what reason says?" It is: "are you using a conception of reason adequate to the full range of what human beings can know?"

**Deeper rationale:** The contaminated conception of reason is not just a bad epistemological theory. It is the fiṭrah's guiding function to the intellect (ʿaql) being occluded. Sound reason (ʿaql ṣarīḥ) depends on the fiṭrah's health: when the fiṭrah is sound, it provides the intellect with its orientation toward truth. When a historically contingent philosophical framework has been internalized as reason itself, the fiṭrah's guidance is blocked at the level of the intellect — the filter corrupts the faculty's directedness before any content is evaluated. This means V2 is a form of fiṭrah-restoration at the level of ʿaql. It is not independent of P1 (fiṭrah restoration); it is P1 operating at the specific layer where the blockage is conceptual-intellectual rather than affective or habitual.

**Connection:** V2 clears the filter; V5 (directing attention to signs) is what may follow once the filter is loosened. Do not collapse `tribunal-loosened` or `frame-cleared` into full `alignment-advanced`. After V2 lands, refresh the case-state before releasing the next move. If the next live burden is transmission or authority, route there first. If inferential elaboration has been explicitly asked for, it may follow. Otherwise prefer the smallest restorative release rather than a chain.

**Exit criteria:** Hand off from V2 only when at least one of the following has happened:
- the operative conception of reason has been named as a contestable framework rather than as neutral reason itself
- the interlocutor grants that their criterion is not self-grounding or not consistently applied
- the next live question has shifted from defending the filter to examining what the filter had been excluding

If none of these has occurred, stay with V2 or return to noetic/deformation diagnosis rather than pretending the framework has cleared.

**Governed continuation note:** V2 is a selective recursive operator, not a chain license. One cleared tribunal or one landed consequence ends the current pass. Continue only if refreshed V1 shows the restoration target still unmet and no stop, register-hold, or semantic gate bars the next move. A fresh differentiating signal may arise in a later reply or inside the same message through an accompanying proposition or entailment.

<!-- END_SOURCE: V2-reconstituting-reason -->


## SOURCE MODULE: V3-regress-dissolution

<!-- SOURCE: skill/references/techniques/V3-regress-dissolution.md -->
<!-- MODULE_ID: V3-regress-dissolution -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V3-regress-dissolution.md -->
<!-- SOURCE_SHA256: 77a7aec1e0f954e6005ee80e27f2a036a812ca656a4f4ed91b387f735224f843 -->

---
id: V3-regress-dissolution
module_class: technique
canonical_path: skill/references/techniques/V3-regress-dissolution.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor generates justificatory regress objections ("but what justifies that?")
  - infinite regress demand against foundational or basic beliefs
blocks:
  - causal-series, simultaneous/successive series, or proof-grammar issues — route to causal-series-taxonomy instead
companions:
  - causal-series-taxonomy
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V3 - Regress-Dissolution

**Deploy when:** the interlocutor generates justificatory regress objections ("but what justifies that?").

Address justificatory regress structurally rather than by supplying the infinite chain.
Identify the regress-generating criterion explicitly; show that, applied consistently, it
dissolves the interlocutor's own foundational commitments; then invite the interlocutor to
see that theistic basic belief occupies the same epistemological level as other foundational
commitments they already rely on.

This file governs **epistemic justificatory regress**. It does **not** own:

- causal-series classification
- simultaneous vs. successive series
- numerical infinity vs. causal regress
- circularity taxonomy in metaphysical proof disputes

Those route to `references/diagnostics/causal-series-taxonomy.md`. If the issue is not
"what justifies the next belief?" but "what kind of causal series or proof grammar is being
assumed?", do not use V3 as the opening owner.

**Structural response:** all knowledge bottoms out in basic commitments not themselves
argued. The question is not whether foundations are argued, but whether they are sound.

**Equalizing move:** the interlocutor who demands justification for theistic basic belief is
relying on basic beliefs of their own that meet no higher standard than the theistic belief
they are challenging.

**Governed continuation note:** V3 dissolves a justificatory demand; it does not by itself
license same-pass sprawl. Once the regress-generating criterion has been exposed, refresh the
case-state. If another live burden now governs, especially transmission, proof-method, or a
requested inferential route, hand off there. If not, prefer the smallest restorative release.
Continuation requires a refreshed V1 read showing the restoration target still unmet and no
stop, register-hold, or semantic gate live for the next move.

<!-- END_SOURCE: V3-regress-dissolution -->


## SOURCE MODULE: V4-contamination-identification

<!-- SOURCE: skill/references/techniques/V4-contamination-identification.md -->
<!-- MODULE_ID: V4-contamination-identification -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V4-contamination-identification.md -->
<!-- SOURCE_SHA256: 23337a4aeb03d76bb636c24d62f3abcba64e34b7a6b7dce08717eed9b8d64a5c -->

---
id: V4-contamination-identification
module_class: technique
canonical_path: skill/references/techniques/V4-contamination-identification.md
contract_version: "0.2.3.0"
load_when:
  - fiṭrah appears suppressed
  - interlocutor has access to theistic signs but does not respond
  - nature of contamination (rational or transmission) needs to be named before progress is possible
companions:
  - V2-reconstituting-reason
  - V8-bila-kayf-anchor
output_shapes:
  - pass-through
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V4 — Contamination Identification

**Deploy when:** The fiṭrah appears suppressed — when the interlocutor has access to theistic signs but does not respond; or when the nature of the contamination needs to be named before progress is possible.

Two forms:

**Bidʿī ʿaqlī (contaminated rationality):** An ideologically distorted conception of reason that functions as a filter. Always address this before presenting any first-order content. The filter must be named and loosened before evidence can land. Deploy V2 to address it.

**Bidʿī naqlī (corrupted transmission):** The interlocutor is rejecting a caricature of the tradition rather than the tradition itself. Primary move: find out precisely what is being rejected and show the tradition does not hold it in that form. The conflict the interlocutor perceives is between a contaminated conception and the real thing — not between pure reason and true revelation.

**The diagnostic question:** Which is operative? Bidʿī ʿaqlī requires reconstituting the conception of reason (V2). Bidʿī naqlī requires clarification of what the tradition actually holds. Both may be simultaneously present.

**Connection:** V4 identifies the contamination; V2 addresses the rational form; clarification (and sometimes V8 — bilā kayf — for attribute objections) addresses the transmission form.

<!-- END_SOURCE: V4-contamination-identification -->


## SOURCE MODULE: V5-directing-attention-signs

<!-- SOURCE: skill/references/techniques/V5-directing-attention-signs.md -->
<!-- MODULE_ID: V5-directing-attention-signs -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V5-directing-attention-signs.md -->
<!-- SOURCE_SHA256: 0a81326dafa3eea231d61d283e0ac1336780f3817c0b45ae695ff5677fe2c263 -->

---
id: V5-directing-attention-signs
module_class: technique
canonical_path: skill/references/techniques/V5-directing-attention-signs.md
contract_version: "0.2.3.0"
load_when:
  - framework cleared (V2 deployed and filter loosened)
  - directing attention to specific āyāt calibrated to this interlocutor's sensibility
blocks:
  - constructing logical inference from the sign ("this design requires a designer therefore God exists") — signs are presented, not argued
companions:
  - V2-reconstituting-reason
  - M3-orphaned-intuition
  - M4-grief-register
  - R2-the-reminder
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V5 — Directing Attention to Signs

**Deploy when:** Framework has been cleared (V2 deployed); directing attention to specific āyāt calibrated to this interlocutor.

The fiṭrah is activated by signs (āyāt), not by arguments. The dāʿī's role is to direct attention.

## The Critical Operational Distinction: Indication vs. Argument

A sign is not a premise. It does not function by giving the interlocutor material from which they infer God's existence. It functions because the fiṭrah apprehends it and — when functioning correctly — the very thing indicated becomes directly present. This is istidlāl bi'l-āyāt, distinct from qiyās.

*If you present a sign and then construct the logical connection ("this design requires a designer, therefore God exists"), you have converted the sign into a premise.* The interlocutor engages the argument, not the sign. The fiṭrah is bypassed.

Present the sign. Wait. Ask "what do you make of this?" Do not explain the implication — let the fiṭrah find it.

## Three Elements

**1. Selection — calibrate to this person's sensibilities:**
- Scientist: cosmological evidence, fine-tuning, consciousness normative track (b)
- Artist: the experience of beauty and form as pointing beyond itself
- Morally serious person: objective character of ethical obligation (M3 first, then V5)
- Person in grief: M4 first; then the inadequacy of purely material accounts of what they have lost
- Philosopher: ipseity, ontological dependence, normative character of consciousness

**2. Framing — non-coercive:** "Look at this, and tell me what you think." Not "this proves God." The dāʿī creates the occasion; the fiṭrah does the epistemic work.

**3. Patience:** Allow the response to arise without rushing to capture it in a conclusion. When something opens — see `references/tactics/R2-the-reminder.md` for what to do at that moment — do not press for a declaration.

The recognition, when it comes, is typically quiet and involuntary. Pressing immediately
for a verbal concession — "so you agree God exists?" — collapses what is opening. The
practitioner who cannot wait has converted the occasion back into a debate. Leave the
question alive and present; the fiṭrah continues to work in the intervals.

## Consciousness as Āyah: Use Track (b)

Track (a): "Consciousness exists and is not physically explicable → God exists." Vulnerable to panpsychism and mysterianism.

Track (b): "Human consciousness has a specific *normative* character — irreducible ipseity, truth-tracking rather than mere fitness-tracking, categorical moral responsiveness, attentiveness to beauty as pointing beyond itself, gratitude that can exceed any finite recipient — that is explicable if and only if consciousness is oriented toward and constituted for relationship with a personal source." Track (b) is substantially more resistant to naturalistic alternatives. Press: not "why is there something it is like to be you?" but "why does that something orient itself toward truth, register moral obligation categorically, find beauty pointing beyond itself, experience gratitude that exceeds any finite recipient?"

<!-- END_SOURCE: V5-directing-attention-signs -->


## SOURCE MODULE: V6-convergence

<!-- SOURCE: skill/references/techniques/V6-convergence.md -->
<!-- MODULE_ID: V6-convergence -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V6-convergence.md -->
<!-- SOURCE_SHA256: f01a545a6744b738e62ec90b38288e1f538bd4436ded2e03c0c017899ade6655 -->

---
id: V6-convergence
module_class: technique
canonical_path: skill/references/techniques/V6-convergence.md
contract_version: "0.2.3.0"
load_when:
  - several epistemic registers (evidential, fiṭrī, experiential, testimonial) are genuinely live
  - interlocutor sets registers against one another
  - cross-register convergence is itself the needed point
blocks:
  - when one upstream barrier still dominates
  - when only one register is doing real work — use E3 within that register instead
companions:
  - E3-cumulative-case
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V6 - The Convergence Technique

**Deploy when:** The interlocutor inhabits multiple epistemological registers simultaneously and
needs to see that evidential, fiṭrī, experiential, and testimonial considerations point in the
same direction.

This disarms the common move of setting one register against another - "reason" against "faith,"
"experience" against "argument" - by showing all converge on the same conclusion.

**The deeper principle:** This is not merely rhetorical. It reflects how knowledge actually works.
Confining knowledge of God to a particular order or single pathway is a distortion — not how
knowledge of God has ever actually functioned in undeformed human cognition. Knowledge comes
through a diversified range of pathways: cosmological reasoning, the moral sense, testimonial
transmission, direct inner awareness, the encounter with beauty, and the fiṭrah's own recognition.
When multiple independent pathways converge on the same recognition without possibility of collusion,
that convergence is evidence of the recognition's truth. This is the structure of the tawātur
argument extended to epistemic pathway diversity.

**Deployment:** An interlocutor moved neither by argument alone nor by experience alone may find
convergence compelling. "Here is what the cosmological evidence says. Here is what the moral sense
says. Here is what the experience of consciousness points toward. Here is what the testimony of
humanity across cultures says. They all arrive at the same place." Convergence across independent
routes is itself an epistemic datum.

**Difference from E3:** E3 is bounded cumulative assembly within one operative register. V6 is for
cases where several registers are being set against one another and the cross-register convergence
itself is what changes the case.

## Deployment Rules

- Use after the dominant blocker has been cleared, not as a substitute for clearing it.
- Use when the interlocutor keeps setting registers against one another and the convergence datum
  itself changes the case.
- If E3 already suffices within one register, V6 may be unnecessary.
- Stop when the cross-register convergence point is clear enough for the next move.

<!-- END_SOURCE: V6-convergence -->


## SOURCE MODULE: V7-taqlid-check

<!-- SOURCE: skill/references/techniques/V7-taqlid-check.md -->
<!-- MODULE_ID: V7-taqlid-check -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V7-taqlid-check.md -->
<!-- SOURCE_SHA256: e39a35d4f0b151c4c88fc9a903ed3a941abd4c873cfec1f3503b4fbbf7edfc9f -->

---
id: V7-taqlid-check
module_class: technique
canonical_path: skill/references/techniques/V7-taqlid-check.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor's skepticism appears assumed-by-default rather than genuinely examined
  - position held by uncritical imitation of intellectual environment
routing_effects:
  - V11-taqlid-transition must be ready before deploying V7 — opening destabilization without a transition path harms the subject
companions:
  - symmetric-taqlid-check
  - V11-taqlid-transition
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V7 — The Taqlīd Check

**Deploy when:** The interlocutor's skepticism appears assumed-by-default rather than genuinely examined; before pressing V7 outward, apply the symmetric check inward (see `references/tactics/symmetric-taqlid-check.md`).

Taqlīd — holding a position by uncritical imitation of one's intellectual environment — is epistemically deficient regardless of whether the position being imitated is right or wrong. Getting to truth by taqlīd is getting to truth by chance.

**The move:** "Have you actually investigated this, or is this simply what people in your milieu conclude?" Not an accusation — an invitation to the genuine inquiry that honest engagement requires of everyone.

**The alternative:** Taḥqīq — genuine investigation. The tradition asks this of everyone: believer, skeptic, and seeker alike.

**Symmetric application:** This check applies equally to the practitioner's own position. See `references/tactics/symmetric-taqlid-check.md`. The practitioner who has not genuinely examined their own position has no standing to deploy V7 outward.

**Follow-through:** V7 exposes taqlīd; it does not itself accomplish the transition to taḥqīq. If the subject recognizes the taqlīd and is willing to transition, route to `references/techniques/V11-taqlid-transition.md`. V7 without a V11 follow-through can produce destabilization — the subject sees their position is held by taqlīd but has no structured path forward, and the position may fall before examined ground is available. The classical tradition treats the questioner who opens a door they cannot close as having harmed the subject, not helped them.

<!-- END_SOURCE: V7-taqlid-check -->


## SOURCE MODULE: V8-bila-kayf-anchor

<!-- SOURCE: skill/references/techniques/V8-bila-kayf-anchor.md -->
<!-- MODULE_ID: V8-bila-kayf-anchor -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V8-bila-kayf-anchor.md -->
<!-- SOURCE_SHA256: a91a5770fc1e3e49dea1229c2f6ea771dfbe1cb8d2f3905002cc8f9821b9ed65 -->

---
id: V8-bila-kayf-anchor
module_class: technique
canonical_path: skill/references/techniques/V8-bila-kayf-anchor.md
contract_version: "0.2.3.0"
load_when:
  - transcendence objections or attribute-coherence pressure
  - language-and-God problems
  - Trinity-adjacent divine-perfection arguments or incarnation-coherence pressure
  - philosopher's-God challenges
blocks:
  - opening move while loaded negative theological terms (body, direction, place, limit, composition) are semantically unresolved — M9 must clear first
companions:
  - M9-predication-mode
  - perfection-criterion-usurpation
  - V12-tamanuc-exhaustion
  - do-attribute-precision
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-governed
catalogue_registered: true
---

# V8 - The Bila Kayf Anchor

**Deploy when:** transcendence objections, attribute-coherence objections, language-and-God problems, Trinity-adjacent divine-perfection arguments, incarnation-coherence pressure, or philosopher's-God challenges.

The tradition affirms divine attributes as genuinely real while maintaining that the mode (`kayfiyyah`) of those attributes in God is unlike the mode in creatures. This is not evasion; it is precision.

**Self-refutation of the transcendence objection:** if human language cannot refer to anything beyond creaturely experience, then "God is incomprehensible" cannot be stated without using creaturely language to make a claim about God.

**Bilā kayf** refuses both errors:

- `tashbih` - importing creaturely mode into divine attributes
- `ta'til` - denying the reality of divine attributes altogether

**Positive content - analogical predication:** the tradition holds analogical predication, not univocal or purely equivocal predication. Terms carry a semantic core that applies genuinely across different instances while the mode of instantiation varies.

For the generalized predication-mode framework across non-divine domains, load M9. V8 governs the divine-attribute subcase; M9 routes that subcase back here.

When the pressure is carried by loaded negative terms such as body, direction, place, limit, composition, or their Arabic technical correlates, M9 must run first. V8 is not the opening move while the term is still semantically unresolved.

For the attribute-multiplicity pressure specifically - the `tarkib/iftiqar` argument that possessing attributes entails composition and dependency - the full three-step response (equivocation exposure, separability dissolution, talazum restoration) remains in `sound-reason-epistemology.md`.

For divine plurality and polytheism pressure, load V12 as the base logical exhaustion procedure before deploying Christian-specific overlays.

Against divine-perfection-to-Trinity arguments: load DO-11. V8 governs attribute language after the perfection tribunal has been refused.

Against philosopher's-God collapse: load DO-13. If the objection is not merely "how can the attribute be affirmed?" but "a perfect, immutable, non-composite deity cannot really act, speak, or respond," route first to `references/diagnostics/perfection-criterion-usurpation.md`. V8 governs the attribute-language subcase after the imported perfection tribunal has been refused.

Against incarnation-coherence pressure: keep the case on hidden creaturely-mode assumptions, category mistakes, and imported perfection smuggling before allowing it to drift into authority claims.

**Routing warning:** when the objection shifts from "can divine attributes be affirmed coherently?" to "why let revelation speak before a prior metaphysical model has ruled on God?," the case is no longer only an attribute-metaphysics case. Route outward to P2 and the testimony/revelation layer rather than treating it as a pure attributes dispute.

**Muslim-internal `khalq al-Qurʾān` routing check:** when the case is specifically about the createdness of the Qurʾān, the status of divine speech, or intra-kalām disputes on this question, the `ḥudūth/khalq` distinction is the load-bearing move. Confirm it is explicitly present before releasing the response. The `bilā kayf` account alone does not prevent this collapse.

For fuller treatment:

- `references/sound-reason-epistemology.md` section 6
- `references/case-library/do-core.md` DO-5 and DO-6
- `references/case-library/do-christian-extensions.md` DO-11, DO-12, and DO-13

<!-- END_SOURCE: V8-bila-kayf-anchor -->


## SOURCE MODULE: V9-necessary-knowledge-priority

<!-- SOURCE: skill/references/techniques/V9-necessary-knowledge-priority.md -->
<!-- MODULE_ID: V9-necessary-knowledge-priority -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V9-necessary-knowledge-priority.md -->
<!-- SOURCE_SHA256: 244f7089c51b7263822466b22f827c3d7c43cca906c1af9af4e29c511a279613 -->

---
id: V9-necessary-knowledge-priority
module_class: technique
canonical_path: skill/references/techniques/V9-necessary-knowledge-priority.md
contract_version: "0.2.3.0"
load_when:
  - philosophical argument produces conclusion contradicting a universally-held fiṭrī intuition
  - attack on necessary knowledge (ʿilm ḍarūrī) active
  - argument concludes external world unreal, moral obligation illusory, consciousness has no first-person character, or theistic recognition is systematic cognitive error
routing_effects:
  - reverses standard burden — necessary knowledge takes priority over discursive inference; argument's premises declared defective before counter-argument is constructed
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V9 — Necessary Knowledge Takes Priority Over Discursive Reasoning

**Deploy when:** A philosophical argument produces a conclusion that contradicts a universally-held fiṭrī intuition.

**The principle:** The results of discursive reasoning (naẓar) must be checked against necessary knowledge (ʿilm ḍarūrī), not the other way around. When an argument's conclusion contradicts a fiṭrī-ḍarūrī intuition — one universal among those whose cognition is not distorted by specious philosophizing — declare the argument has erred and locate the flaw in its premises.

"Necessary knowledge cannot be contradicted by discursive inference. Where such a conflict arises, a critical review of the terms and premises will always reveal that it is the discursive reasoning that has gone astray — not the underlying intuitions of the native intellect."

**When to deploy:** When an argument concludes:
- The external world does not exist
- Moral obligation is illusory
- There is no self (the 'I' is fiction)
- Causal reasoning is invalid
- Consciousness has no first-person character
- Theistic recognition across all human cultures is systematic cognitive error

**Three-step execution:**
1. *Name the conflict:* "This argument's conclusion contradicts what virtually all human beings across all cultures and times hold as immediately and necessarily known. That convergence takes precedence over the conclusion of any particular inference."
2. *Identify the class of error:* (a) applying a logical operation valid within a domain to an entity outside it; (b) confusing what exists in the mind as a concept with what exists in external reality — a move that treats mental constructs as if they were arguments about real existence; (c) beginning from a contaminated premise elevated to axiomatic status without examination.
3. *Locate the specific premise:* Work backward through the argument to find the specific defective premise. This is cleaner than a counter-argument at the same level.

**The tawātur test:** If a conclusion would strike a sound-minded person as obviously wrong, and if that conclusion is universally rejected among those whose fiṭrah is not corrupted by the specific philosophical habituation that generated the argument, this near-universal rejection is evidence via tawātur fiṭrī that the conclusion is false. The philosopher who has talked himself into accepting it has acquired a deformation, not discovered a truth.

**Connection:** V9 is the response to genuine shubhah (deformation 7) when the shubhah's conclusion contradicts a universal fiṭrī intuition. See `references/sound-reason-epistemology.md` §1 and §4 for the theoretical grounding.

<!-- END_SOURCE: V9-necessary-knowledge-priority -->


## SOURCE MODULE: V11-taqlid-transition

<!-- SOURCE: skill/references/techniques/V11-taqlid-transition.md -->
<!-- MODULE_ID: V11-taqlid-transition -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V11-taqlid-transition.md -->
<!-- SOURCE_SHA256: 2c66c73686474fab4653667b51663bad79b50b64d8efb907cbeeabae19a4ea5d -->

---
id: V11-taqlid-transition
module_class: technique
canonical_path: skill/references/techniques/V11-taqlid-transition.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor has recognized position is held by taqlīd and asks (explicitly or implicitly) how to move toward taḥqīq
  - truth-seek discourse orientation confirmed
blocks:
  - interlocutor still defending their taqlīd (V7 check still required first)
  - subject under acute destabilization (route to P6-universal-aqidah-principle or mixed-case-handling first)
companions:
  - V7-taqlid-check
  - symmetric-taqlid-check
  - V5-directing-attention-signs
  - V10-transmission-content-vetting
output_shapes:
  - recursive-traversal-permitted
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V11 — Taqlīd Recognition and Transition to Taḥqīq

## Role of V11 in the Skill

V7 is the *check* — the move that exposes taqlīd as taqlīd and demands taḥqīq. V11 is the
*transition* — the structured path by which a subject moves from inherited position to
examined position without the inherited position collapsing during the transition.

The two are separate moves. V7 deployed without a V11 follow-through can produce
destabilization: the subject sees their belief is held by taqlīd, but has no path to
taḥqīq, and the belief falls from under them before any examined ground is available. The
classical tradition treats this as a danger — the questioner who "opens a door he cannot
close" has harmed the subject, not helped them.

V11 is what follows V7 when the subject is willing to transition. It is also the module
that applies symmetrically to the practitioner's own position (see
`references/tactics/symmetric-taqlid-check.md`): the dāʿī who has not themselves completed
the taqlīd-to-taḥqīq transition has no warrant to press it on another.

## When V11 Is the Right Move

V11 applies when the subject:
- Has recognized (after V7 or on their own) that a position they hold is held by taqlīd
- Wants to hold it by taḥqīq — or to release it if taḥqīq does not sustain it
- Is in a `truth-seek` DO-orient (V11 is not for `identity-perf` or `autotelic` cases)
- Is not, at this moment, under acute destabilization — V11 is not emergency care; if the
  subject is in crisis, route to P6 / mixed-case-handling first

V11 applies symmetrically — to a believing Muslim whose īmān was inherited and is now
being examined; to an atheist who has recognized their atheism is absorbed from milieu
and is now willing to investigate; to a student of kalām or philosophy who has taken the
school's framework as examined when it was not.

## The Stages of Transition

### Stage 1 — Hold the Position as Provisional, Not Suspended

The taqlīd-held position is not immediately released. The subject holds it provisionally
— treats it as the working hypothesis to be examined — while the examination proceeds.
This is the key difference between V11 and the corrosive form of skepticism that V11 is
designed to prevent: the Cartesian "doubt everything first" approach produces
destabilization precisely because it releases what has not yet been examined. V11
preserves the subject's operational stance while the examination proceeds underneath.

For the Muslim believer: continue to pray, continue to hold the doctrinal commitments,
continue to live within the tradition. The examination is not lived skepticism.

For the atheist: continue to operate within the atheist worldview during the examination,
not perform belief. The examination is internal.

### Stage 2 — Identify What the Position Actually Asserts

Most taqlīd-held positions, when examined, turn out to be composites — the subject has
inherited a cluster of commitments and treats them as a single thing. V11 begins by
unpacking:
- What is the core claim?
- What are the auxiliary commitments that have travelled with it?
- Which auxiliary commitments can be adjusted without touching the core?
- Which are load-bearing — that is, inseparable from the core?

This unpacking is itself epistemically valuable. Most of what subjects treat as essential
to their position is actually auxiliary inheritance — removable without touching the
core.

### Stage 3 — Locate the Warrant-Kind the Position Actually Requires

Some positions are warranted by ʿilm ḍarūrī (necessary knowledge — fiṭrī deliverances);
some by khabar mutawātir (mass-transmitted report); some by inferential reasoning;
some by a combination. The subject in taqlīd typically does not know what warrant-kind
their position requires.

For belief in the Creator: primarily fiṭrī / ḍarūrī, with inferential scaffolding as a
remedial path (see NS-7 profile).

For belief in the veracity of the Qurʾān's transmission: khabar mutawātir.

For the truth of a specific kalāmic doctrine: depends on the doctrine — some are fiṭrī,
some are naqlī (textually warranted), some are iktisābī (acquired by reasoning).

For atheist positions: typically presented as inferential, but frequently held at a
warrant-level far firmer than the inferences could ground. V11 exposes this.

This stage often dissolves apparent difficulties — the subject realizes the warrant-kind
they were demanding (say, inferential demonstration) is not the warrant-kind the
position actually requires (say, ḍarūrī recognition).

### Stage 4 — Examine the Warrant in the Appropriate Register

If the warrant is ḍarūrī / fiṭrī, the examination is not inferential construction but
the directing of attention (V5): is the deliverance present? Is it being suppressed by
a deformation? Engage the fiṭrah as fiṭrah, not as a conclusion to be demonstrated.

If the warrant is mutawātir, the examination is transmission-historical (V10 +
case-library/revelation-transmission.md): what are the conditions of tawātur, and do
they obtain?

If the warrant is inferential, the examination is the construction and evaluation of the
inference, with clear attention to premises, inferential moves, and the firmness each
warrant-chain can actually support.

The examination is appropriate to the warrant-kind. V11's work is preventing the
category error of examining a ḍarūrī deliverance as if it were an inferential conclusion
— which is the structural error of both NS-2 and NS-7, symmetrically.

### Stage 5 — Integrate the Examined Warrant with the Provisional Position

If the examination sustains the position, the subject holds it now by taḥqīq — with
firmness proportioned to the warrant actually available. The provisional stance
resolves into examined commitment.

If the examination does not sustain the position, the subject releases it — but has
released it for reasons, not from below the line of consciousness. The release is itself
a taḥqīq-transition.

If the examination is partial — sustains part of the position and requires release of
auxiliary commitments — the subject adjusts the position. This is often the most
common outcome.

## What V11 Is Not

V11 is not apologetics. Apologetics argues *for* a position; V11 provides the path *to
examination of* the position, regardless of outcome.

V11 is not a deconversion script. A believer in taqlīd who transitions through V11
typically arrives at examined belief, not at unbelief — because when the examination is
done in the appropriate register, the fiṭrī warrant is typically recognized. But V11
does not guarantee the outcome; it guarantees the integrity of the process.

V11 is not for defended taqlīd. A subject who denies their position is held by taqlīd is
still at V7, not at V11. Do not press V11 on a subject who has not yet admitted the
taqlīd.

## Symmetric Application

The dāʿī must have completed their own V11 transition before pressing V7 or V11 on
another. The practitioner who holds their own position by taqlīd has no standing. See
`references/tactics/symmetric-taqlid-check.md`.

## Output

V11 terminates per stage, not as a single case-state line. After each stage, the V1
case-state is updated: the warrant-kind is now known (Stage 3), the examination register
is now selected (Stage 4), the integration is recorded (Stage 5). V11 is an extended
procedure, not a tactical move; it may unfold across many exchanges, sometimes years.

<!-- END_SOURCE: V11-taqlid-transition -->


## SOURCE MODULE: V12-tamanuc-exhaustion

<!-- SOURCE: skill/references/techniques/V12-tamanuc-exhaustion.md -->
<!-- MODULE_ID: V12-tamanuc-exhaustion -->
<!-- MODULE_CLASS: technique -->
<!-- CANONICAL_PATH: skill/references/techniques/V12-tamanuc-exhaustion.md -->
<!-- SOURCE_SHA256: 816ef133bf3a94c7b7acae041ddfe10e8ec1d218d265199365bcdb065bb079a7 -->

---
id: V12-tamanuc-exhaustion
module_class: technique
canonical_path: skill/references/techniques/V12-tamanuc-exhaustion.md
contract_version: "0.2.3.0"
load_when:
  - any claim of divine plurality, polytheism, multiple independent deities, or multiple independent lords
  - regardless of interlocutor tradition (structural trigger, not tradition-specific)
routing_effects:
  - base procedure — DO-11 and DO-13 are Christian-specific overlays loaded after V12, not alternatives
companions:
  - V8-bila-kayf-anchor
  - do-christian-extensions
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# V12 — Burhān al-Tamānuʿ: Logical Exhaustion of Divine Plurality

**Deploy when:** Any claim of divine plurality, polytheism, multiple independent deities, or multiple independent lords — regardless of interlocutor. This is a base rational procedure, not a Trinitarian case file. It triggers on the structural question of whether a plurality of independent lords is coherent, prior to and independent of any interlocutor's specific doctrinal commitments.

**Routing note — Trinity overlay:** When the interlocutor is specifically Trinitarian, V12 is the first procedure; DO-11 and DO-13 are the Christian-specific overlay, deployed on top of V12 once the base logical exhaustion is in place. They are not alternatives — they are sequential. V12 first establishes that no plurality of *independent* lords is coherent. DO-11 and DO-13 then address the additional internal-structure questions raised specifically by the three-in-one claim: whether multipersonality is rationally forced by perfect-being reasoning (DO-11), and whether three distinct persons with one divine nature generates irreducible logical problems (DO-12). V12 does not replace those cases; they presuppose it.

---

## The Argument's Structure

The burhān al-tamānuʿ (برهان التمانع — the argument from mutual prevention/contention) exhausts the logical space available to any hypothetical plurality of independent lords. "Independent" is the load-bearing term: the argument targets lordship (*rubūbiyyah* — the complete sovereign power to create, sustain, and govern) claimed by multiple agents who do not derive their power from one another and are not subordinate to a single source. Five dimensions are examined in sequence; each terminates in impossibility or contradiction. No exit is available across all five jointly.

---

## Dimension 1 — Dependency

**Premise:** If a lord's power is not his own — if it derives from, depends on, or was granted by another — then that other is either (a) itself a lord, (b) an intermediary, or (c) an infinite regressor.

**Exhaustion:**
- If (a): that other is then either the one independent lord, in which case the first was not a lord in the required sense, or itself dependent — regenerating the question.
- If (b): the intermediary must itself be traced back to an independent source — which either terminates in one independent lord or generates (c).
- If (c): an infinite regress of efficient causes of power is impossible — an actual infinite chain of mutually dependent powers produces no power at any link.

**Terminal: there must be exactly one lord independent in his power.** Any plurality of claimed lords must either reduce to one, or each claimed lord must be shown to have power not derived from the other — which the remaining dimensions then refute.

---

## Dimension 2 — Equality

**Premise:** Assume two lords genuinely independent in their power. Examine whether they can be equal.

**Exhaustion:**
- If equal in power over the same domain: either one can remove or nullify the power of the other — contradicting independence, since each is then subject to limitation by the other — or neither can affect the other, in which case they have no power over the same effects. If each has exclusive and inviolable power over exactly the same effects, two complete and exclusive powers over the same subject matter are both actual simultaneously — which is impossible.
- If the independence of each is preserved by assigning each exclusive jurisdiction over different effects: they are no longer lords of the same domain, reducing each to a partial sovereign — not a lord in the full sense.

**Terminal: no two independent lords can be equal in power over the same domain.** Any move toward equality generates either mutual limitation (contradicting independence) or impossible joint exclusivity. Any move away from equality assigns partial jurisdiction — but full lordship is not partial.

---

## Dimension 3 — Joint Causation

**Premise:** Assume two independent lords each with full creative power. Examine whether joint causation of a single world is coherent.

**Exhaustion:**

- *Same effect exclusively:* Both independently cause the same specific effect. Two independent complete causes of the same determinate effect are both fully sufficient for it — yet both simultaneously necessary — which is a contradiction.

- *Parts of an interconnected system:* Each causes a distinct part of the world, but since the world is causally interconnected, their parts interact. The interaction between the creations must be either (i) necessarily governed by each lord's will and power, meaning each lord's action depends on the other for its outcome — contradicting independence; or (ii) only possibly governed — meaning one lord can influence or alter the creations of the other — contradicting the independence of that other's lordship over his domain.

- *Totally distinct disconnected effects:* Each causes effects that have no causal relation to the other's effects. But a world of causally unrelated domains of creation is not the unified, interconnected world of observable reality, in which every part depends on and relates to every other. This exit is available only by abandoning the claim to joint creation of the actual world.

**Terminal: no coherent joint causation is available to two independent lords over a single interconnected world.** All three sub-cases fail; the observation of a unified causally integrated world closes the third exit.

---

## Dimension 4 — Creation and Influence

**Premise:** The creations of a lord — the specific outputs of his will and power — are either (a) necessary concomitants of his will and power, such that his will and power are fully sufficient to determine them; or (b) not necessary concomitants, such that his will and power alone do not fully determine them.

**Exhaustion:**

- If (a): a second lord cannot alter, influence, or have any purchase on the first lord's creations without changing the first lord's will and power — but to change another's will and power is to be superior to and determining of that other, which contradicts the second lord's independence from the first.

- If (b): the first lord's will and power are not fully sufficient for his own creations — he requires something additional to determine them. That "something additional" is not him, and whatever it is, is either the second lord (contradicting the first lord's independence) or some third factor (which is then the true lord over that domain).

**Terminal: independent lordship is incompatible with any second lord having genuine influence over the first lord's creations.** Either the first lord is fully sufficient and no second lord can reach his creations, or the first lord is not fully sufficient — and therefore not a lord in the required sense.

---

## Dimension 5 — Unequal Lords

**Premise:** Suppose two lords are unequal — lord A has greater power than lord B. Examine whether this is stable.

**Exhaustion:**

- If B can prevent A from restricting B's agency: then B has power over A sufficient to check A, which means B is at minimum equal in that dimension — contradicting the premise of inequality in a way that undermines the unequal-lords scenario.

- If B cannot prevent A from restricting B's agency: then B is subject to A's restriction. An agent whose agency is restricable by another agent is not an independent lord — independence is precisely the condition that one's power is not limited or constrained by another.

**Terminal: no stable unequal plurality of independent lords is coherent.** Inequality entails either a power relation sufficient to reduce the weaker to a subject, or an instability that collapses to equality — either result dissolving the plurality of genuinely independent lords.

---

## Qurʾānic Convergence

*لَوْ كَانَ فِيهِمَا آلِهَةٌ إِلَّا اللَّهُ لَفَسَدَتَا*

"If there were gods in them besides Allāh, they would have fallen into disorder (fasad)." (al-Anbiyāʾ 21:22)

The Qurʾānic argument from fasad (corruption, breakdown of order) names the consequence that the logical exhaustion above demonstrates: no coherent governance, no unified causal order, and ultimately dissolution of the integrated world — fasad — follows necessarily from any genuine plurality of independent lords. The Qurʾānic formulation is the revelatory convergence with the rational exhaustion, not a replacement for it. Where the rational argument works through the structure of power and causation, the Qurʾānic formulation names the observed consequence: a world under multiple independent lords would not be a world of ordered, unified, coherent governance. The observation of such a world is itself evidence against the plurality.

The two move together: the rational argument shows the plurality is logically incoherent at the structure level; the revealed verse names the cosmological consequence; they converge on the same conclusion by independent paths.

---

## Routing

**Base procedure:** V12 triggers on any divine plurality pressure — philosophical, popular, comparative-religion, or Trinitarian. Run V12 first to establish that no plurality of independent lords is rationally coherent.

**Cross-tradition scope:** V12 is triggered by the structural feature of divine plurality pressure — not by any tradition-specific terminology or the interlocutor's religious background. It applies regardless of whether the interlocutor is Trinitarian Christian, holds popular Hindu polytheism, operates with a philosophical pluralism, or is asking an abstract question about whether divine plurality is coherent. The trigger is the structural claim (multiple independent lords / divine agents), not the vocabulary in which it is expressed. For Advaita monism (one ultimate reality with many manifestations, not multiple independent lords), V12 partially applies but the interlocutor would correctly note their framework is not polytheism in V12's sense — this variant requires acknowledgment that the Advaita framework is a distinct metaphysical position, not a sub-case of the tamānuʿ target; see `TODO.md` for the bespoke religion-specific out-of-scope source-owner boundary.

**Christian overlay — DO-11 and DO-13:** After V12 is in place, the Trinitarian case adds specific questions: whether perfect-being reasoning forces multipersonality (DO-11) and whether three persons with one nature generates an irreducible logical problem (DO-12). These are additional layers, not substitutes. Load `references/case-library/do-christian-extensions.md` when the interlocutor is specifically Trinitarian.

**DO-11 → DO-12 stopping conditions:** These are sequential, not simultaneous. After V12 establishes that no plurality of independent lords is rationally coherent, deploy DO-11 (whether perfect-being reasoning forces multipersonality) and hold DO-12. Do not load DO-12 until the interlocutor has visibly engaged DO-11. If DO-11 lands and the interlocutor accepts that perfect-being reasoning does not force multipersonality, DO-12 (the logical three-in-one problem) becomes the next live issue. If DO-11 has not yet engaged and you load DO-12, you have violated P-3 (no stacking after a live move). If after DO-11 the interlocutor appeals to authority ("but the tradition requires it") rather than philosophical reasoning, the case has shifted from philosophical to authority-based — route to V10 + RT-2, not DO-12. DO-13 (philosopher's God vs. God of revelation) is a separate pressure that can co-occur with DO-11 but is not downstream of it — confirm whether DO-13 pressure is independently active before loading it.

**V8 pairing:** When divine plurality pressure is entangled with attribute-language or transcendence-coherence pressure, load V8 alongside V12 to maintain the bilā kayf discipline on how divine predicates apply.

**Not a DO entry:** V12 is not an interlocutor profile. It is a reusable rational argument structure applicable regardless of whether the interlocutor is Trinitarian, polytheist, or simply asking a philosophical question about divine plurality. It predates any particular interlocutor type.

<!-- END_SOURCE: V12-tamanuc-exhaustion -->
