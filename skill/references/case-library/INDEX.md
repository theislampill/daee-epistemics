---
id: case-library-index
module_class: governance
canonical_path: skill/references/case-library/INDEX.md
contract_version: "0.2.2.0"
load_when:
  - selecting or confirming a case-library module after V1 diagnosis
catalogue_registered: false
---

# Case Library — Index and Router

Case-library files are not default entry points. Diagnose first, confirm the case family,
then load only the matched playbook and pair it with the tactic, technique, or procedure
the case still requires.

## Case-Library Discipline

- A case file sharpens a recurring objection family. It does not replace noetic diagnosis.
- Load one case file at a time unless the case genuinely spans two confirmed families.
- Pair case files with techniques and tactics; do not let the case file become the whole response.

## Routing Table

| Confirmed match | File | Do not use when | Typical pairings |
|-----------------|------|-----------------|-----------------|
| NS-1 through NS-12 | `case-library/profiles/[matched-ns-code].md` — see `case-library/profiles/INDEX.md` for routing table | You only have a topic, not a recognizable noetic type | V1, M5, V2, M3 |
| DO-1 through DO-6 | `case-library/do-core.md` | The objection family is not yet distinguished from grief, criterion protest, or testimony critique | M2, V8, P2 |
| DO-7 through DO-10 or DO-15 | `case-library/do-second-loop.md` | The case is still at first-order objection level | M1, V9, P2 |
| DO-11 through DO-14 | `case-library/do-christian-extensions.md` | Trinity, philosopher's-God, or Christian canon-authority pressure has not been classified precisely | V8, V10, P2 |
| RT-1 through RT-4 | `case-library/revelation-transmission.md` | The case has not yet been separated into testimony, text, canon, prophetic-claim, or believer-destabilization layers | V10, P2, P5 |
| Ḥadīth corpus / authentication pressure | `diagnostics/hadith-authentication-epistemology.md` | The case is Qur'anic RT-1..RT-4, or the transmission burden has already been typed and the remaining issue is purely doctrinal | V10, V2, P5 |
| DO-6, DO-11–13 with predication/composition/analogy pressure | `case-library/do-attribute-precision.md` | The attribute objection is a straightforward coherence claim with no predication-type subtlety | V8, sound-reason-epistemology §6.3 |
| Philosophical framework confirmed as upstream tribunal | `case-library/philosophical-usurpation.md` | A framework is held but not yet functioning as an upstream authority — use foreign-premise-detection first | V2, prophecy-wahy-supremacy.md, DO-13 |

### NS Family — Routing Discipline

**What NS codes identify:** The noetic structure of the subject — who the person IS epistemically: what they hold as basic, what their implicit doxastic rule is, what the load-bearing anchor of their belief-structure is. NS is orthogonal to DO: a single person can be NS-1 while pressing a DO-2 argument; knowing their NS type does not determine which argument they are making, and knowing which argument they are making does not determine their NS type.

**Load-sequence note:** Run `references/diagnostics/noetic-reading-checklist.md` first, then identify the NS type, then check discourse orientation via `references/diagnostics/discourse-orientation.md`.

**Correct routing:** NS code is assigned based on the subject's governing epistemic commitments and warrant structure — their implicit doxastic rule, load-bearing anchor, and basic-belief set — not based on the argument they happen to be making.

**Incorrect routing:** Assigning NS-1 because the interlocutor cited a naturalist argument. The argument type does not determine the NS code. A kalāmic evidentialist (NS-6) can cite an evolutionary debunking argument; a habituated atheist (NS-5) can press a hiddenness argument. Match the NS code to the noetic structure, not to the objection content.

**NS vs. DO distinction in practice:** If you find yourself assigning an NS code based primarily on which DO case the interlocutor is pressing, you have collapsed the orthogonal axes. Return to the noetic-reading-checklist and identify what the subject holds as basic before assigning NS.

**NS-10 through NS-12:** These codes cover the profile gaps that previously routed only through specialty diagnostics. NS-10 = Māturīdī Evidentialist; NS-11 = Fideist / Reformed Basic-Belief; NS-12 = Blank-Slate or Dual-Nature Fiṭrah. Full profiles in individual files under `case-library/profiles/`. NS-10 still loads `kalamic-interlocutor.md` for deep treatment; NS-12 still loads `fitrah-perspectives.md`.

---

### DO Family — Routing Discipline

**What DO codes identify:** The objection family of the argument the interlocutor is pressing — the problem family requiring substantive engagement. DO is orthogonal to NS: different NS types can press the same DO argument, and the same person can shift DO families across a conversation.

**Load-sequence note:** Establish NS code and deformation read first. DO entry is selected based on what the noetic structure and deformation allow to land — DO content is the last layer loaded, not the first. Do not route to a DO file before confirming discourse orientation; content deployed into identity-performance or grief-primary register has been loaded before the filter that will absorb it is addressed.

**Correct routing:** Route to the DO entry after the NS code, deformation read, and discourse orientation are established. Confirm the specific DO family before loading: DO families share surface vocabulary (attribute language, transcendence, diversity) but the underlying problem is different in each case.

**Incorrect routing:** Using DO-6 (attribute coherence) as the trigger when the real pressure is DO-13 (philosopher's-God vs. God of revelation), because both involve attribute language. DO-6 (attribute coherence) is about whether divine attributes can be coherently affirmed at all — the incoherence objection to classical theism. DO-13 is about whether the God of revelation must be reinterpreted through the philosophical categories of absolute simplicity and immutability — a competing theistic ontology. Do not collapse these: DO-6 is a semantic-coherence problem; DO-13 is a competing-ontology problem.

**Adversarial near-miss:** Interlocutor cites divine hiddenness (surface: DO-1) but the real governing structure is grief — a personal loss that has been given theological language. The DO-1 philosophical apparatus (sincere-non-belief, epistemic distance, evidence-proportioned belief) does not address the affective register. Misrouting to DO-1 content while grief governs is the Diagnosis Collapse anti-pattern applied to the DO axis. Differentiating signal: does the hiddenness claim have propositional structure with evaluable premises, or is it a felt absence expressed in theological language? If the latter, M4 governs before any DO entry.

---

### DO-Family Routing Architecture

**DO codes identify pressure families, not standalone rebuttal scripts. A DO code alone does not authorize answer release.**

**DO dispatch rule — all six conditions required:**
1. the global diagnostic floor (V1, mandatory Phase 2 passes, diagnostic IR, routing-precedence.md);
2. the confirmed DO family;
3. the family-local load floor;
4. all matched TTP / diagnostic owners justified by the current case-state;
5. output-release / Layer B discipline;
6. P7 stop/hold/recurse discipline.

A confirmed topic family activates its load floor, not merely its named case file.

**Negative routing rules:**
```
Do not route as: "Trinity → do-christian-extensions.md → answer."
Do not route as: "evil → do-core.md → theodicy."
Do not route as: "attribute coherence → do-core.md → V8 → answer."
Do not route as: "canon authority → do-christian-extensions.md → answer."
```

**Correct route shape:**
```
diagnostic gate
→ claim-level / PF / upstream blocker read
→ confirmed DO family
→ family-local load floor
→ matched semantic / authority / proof / register owners
→ DO substantive insight only after upstream gates clear
→ bounded Layer B
→ held downstream material
→ state refresh
```

**DO-family near-miss rules:**
- hiddenness may be grief-primary (M4/P7) rather than DO-1 philosophical hiddenness; run M4 discriminator first
- evil may be protest/grief register (M4/P7) rather than DO-2 evidential argument; do not deploy theodicy into grief
- attribute language may be DO-5, DO-6, DO-13, or a loaded-term lexical trap (M9/definition-discipline first); do not collapse on surface vocabulary
- Trinity pressure may be multiple-independent-lords pressure (V12) before Christian model overlay; confirm context before DO-12
- canon pressure may be authority-certification (V10) before textual content analysis; do not load DO-14 content before V10 runs
- secular neutrality may be criterion-import (V2/FPD/reason-disambiguation) before evidence is live; criterion must be cleared before content
- kalāmic proof demand may be proof-method/authority-order pressure (proof-method-audit.md/kalamic-interlocutor.md) before content; proof grammar is upstream of content

**DO-family load floors** (activate from confirmed routing state, not from surface keywords — not global ambient loads):

| Floor | Activates when | Minimum owners |
|---|---|---|
| Base substantive | confirmed ordinary DO pressure, no higher-order blocker | V1 + Phase 2 passes, IR, routing-precedence.md, matched DO file, matched TTP owner(s), P7 stop check |
| Doctrinal/metaphysical objection | divine attributes, Trinity, incarnation, philosopher's-God, predication, or composition pressure live | M9-predication-mode.md, V8-bila-kayf-anchor.md, do-attribute-precision.md, definition-discipline.md, perfection-criterion-usurpation.md, foreign-premise-detection.md |
| Higher-order / criterion-import | tribunal, criterion, neutrality claim, proof-method requirement, or imported standard governs | reason-disambiguation.md, foreign-premise-detection.md, V2-reconstituting-reason.md, philosophical-usurpation.md, proof-method-audit.md, perfection-criterion-usurpation.md, routing-precedence.md, pattern-profiling.md |
| Transmission / authority | scripture, canon, preservation, church authority, Qur'an transmission, hadith, or authority certification live | V10-transmission-content-vetting.md, revelation-transmission.md, hadith-authentication-epistemology.md, prophetic-discourse-neutralization.md (if revelation formally honored but functionally emptied), do-christian-extensions.md DO-14 for Christian canon |
| Mixed / thin-basis / register-governance | thin basis, grief/identity/autotelic register, or multiple live reads compete | mixed-case-handling.md, case-state-schema.md, P7-restoration-stops.md, M4-grief-register.md, discourse-orientation.md, modes-of-concealment.md, anti-patterns.md |

**Pressure-type → owner routing table:**

| Pressure signal | Required owner route |
|---|---|
| identity/counting/multiplicity | definition-discipline.md; M9-predication-mode.md; do-attribute-precision.md when attribute/person pressure live |
| divine predication / God-language | M9-predication-mode.md; V8-bila-kayf-anchor.md |
| person/nature or attribute multiplicity | do-attribute-precision.md; do-christian-extensions.md after model identification |
| perfection/simplicity/immutability/non-eventfulness tribunal | perfection-criterion-usurpation.md; foreign-premise-detection.md; philosophical-usurpation.md when tribunal confirmed |
| revelation/canon/church-authority fallback | V10-transmission-content-vetting.md; do-christian-extensions.md DO-14; revelation-transmission.md only when RT pressure is Qur'anic |
| multiple independent deities/lords | V12-tamanuc-exhaustion.md before Trinity-specific overlays |
| grief-primary evil/hiddenness | M4-grief-register.md; P7-restoration-stops.md; DO content held |
| moral ontology / orphaned moral intuition | M3-orphaned-intuition.md before evidential moral debate |
| secular neutrality / pseudo-neutral reason | reason-disambiguation.md; foreign-premise-detection.md; V2-reconstituting-reason.md; philosophical-usurpation.md when upstream tribunal confirmed |
| kalāmic naẓar-priority / proof-method pressure | kalamic-interlocutor.md; proof-method-audit.md; reason-disambiguation.md; V2-reconstituting-reason.md |
| loaded negative theological terms | M9-predication-mode.md; definition-discipline.md when technical capture live |
| semantic neutralization of revelation | prophetic-discourse-neutralization.md before first-order interpretation |
| causal-series / regress pressure | causal-series-taxonomy.md; proof-method-audit.md before cosmological proof prose |
| necessity/contingency proof grammar | proof-method-audit.md; causal-series-taxonomy.md if dependency/regress taxonomy live; philosophical-usurpation.md if becomes tribunal |

**Selective routing:** Family-local floors are minimum confirmed loads after routing state justifies them. They are not global ambient loading. Files whose load condition is not met remain unloaded. The fact that a DO family has a fan-out table does not mean every listed owner is active.

Loaded owner ≠ active Layer B content. A file may be loaded because the case-state requires its gate or discriminator, while its substantive content remains held until upstream blockers clear. A triggered downstream owner may be named in `What is withheld and why`, but must not be smuggled into the public answer.

**Under-load guard:** A complex confirmed DO route normally requires more than the named DO file plus one technique. Loading only the visible topic file plus one technique is insufficient for a complex case with semantic, authority, proof-method, register, or tribunal pressure. Those owners must be loaded and represented in the IR even when Layer B output remains short.

Failure example:
```
Bad:  DO-12 → do-christian-extensions.md → V8 → answer.
Required: V1 → Phase 2 passes → IR → routing-precedence → M9/definition-discipline if identity/counting
  terms unstable → V12 if multiple independent lords pressure live → do-christian-extensions.md DO-12
  → do-attribute-precision.md if person/nature/attribute precision live → V8 only after semantic/model
  discipline clears → bounded Layer B.
```

---

### RT Family — Routing Discipline

**What RT codes identify:** Cases about transmission, text, canon, and preservation — cases where the interlocutor is specifically pressing text-history or authority-of-source claims. RT cases are never the primary routing family unless the interlocutor is specifically pressing manuscript, canon-formation, qirāʾāt, or preservation questions.

**Load-sequence note:** Run V10 (transmission and content vetting) before any RT case entry — V10 separates the artifact from the authenticated transmission before any content-level response is given. For RT-4 (believer-destabilization), check whether authority-fatigue or relational harm is co-present before engaging the textual layer; if so, P7 Stop 3 (Relational-Repair-First) may govern before RT content.

**Correct routing:** Route to RT only when the live pressure is specifically on transmission reliability (RT-1), canon authority (RT-2), qirāʾāt/manuscript plurality (RT-3), or believer-destabilization (RT-4). Run V10 before any RT case entry.

**Ḥadīth boundary:** Ḥadīth corpus/authentication cases are not RT-1 through RT-4 and do not emit RT-5. After V10, route them to `references/diagnostics/hadith-authentication-epistemology.md`, then release downstream doctrine only if that owner says the transmission burden is no longer primary.

**Incorrect routing:** Routing to RT-3 because the interlocutor mentioned "the Qurʾān," rather than because they are specifically pressing manuscript, qirāʾāt, or preservation questions. Mentioning a text is not the same as pressing a text-history claim. The RT family requires that text-history, transmission reliability, or canon authority is the live pressure, not merely the subject.

**Adversarial near-miss:** Interlocutor is an NS-9 historical-critical skeptic importing NT text-critical categories and asking about early Qurʾānic codices. The surface looks like RT-1 (manuscript reconstruction). But the live pressure is actually V10's prior question — the imported framework treats all ancient documents through the same criterion, which does not distinguish artifact from authenticated transmission. Routing directly to RT-1 content without first applying V2 (framework-clearing on the imported method) confirms the NT criterion's applicability to the Qurʾānic case. Correct sequence: V2 → V10 → RT-1 sub-route. This is also the NS-9 pattern — check `case-library/profiles/ns-9-historical-critical-skeptic.md` for the full intervention order before loading RT-1.

## Quick NS Identification

| Profile | Marker | Primary deformation | First likely move |
|---------|--------|---------------------|------------------|
| NS-1 Naturalist | "there is no evidence"; causal closure assumed; drift toward sophistic skepticism under consistent pressure | I'tiqadat mawrutha | V2 |
| NS-2 Agnostic Evidentialist | "belief must be proportioned to evidence"; refusal of non-inferential warrant | ẓann; possibly genuine shubhah | E2 plus V3 |
| NS-3 Deconverted | Grievance-stabilized argumentation around a single shubhah; orphaned moral commitments | hawa; zann; possibly gharad | M3 or P4 |
| NS-4 Secular Moral Realist | Moral facts are objective but God is rejected; normativity helped-to without ontology | zann; i'tiqadat mawrutha | M3 |
| NS-5 Habituated Atheist | God's non-existence treated as basic | Primarily hawa; possibly gharad; 'ada | F2 (volitional acknowledgment) first; then M4 if grief-primary, R2 if involuntary recognition near surface, V7 otherwise |
| NS-6 Kalāmic Evidentialist | `dalīl` demand; `wujūb al-naẓar`; taqlīd treated as non-knowledge; narrow necessary-knowledge class | iʿtiqādāt mawrūtha; often ẓann | `diagnostics/kalamic-interlocutor.md` — school identification (Muʿtazilī / Ashʿarī / Māturīdī) is mandatory before committing restoration target; if Māturīdī confirmed, re-assign to NS-10. If divine attributes or speech are live alongside the epistemological pressure, an ontological burden is also present — restoration target and matched modules differ by school (see `kalamic-interlocutor.md` §Downstream Routing Table). Then V2 for epistemological burden; §6.2 + V8 for ontological burden; P3 when reason-vs-revelation is the live framing. |
| NS-7 Theistic Evidentialist | God affirmed; natural-theology apparatus held as the *precondition* for warranted belief; fiṭrī recognition demoted to "mere feeling" | i'tiqadat mawrutha; often zann | V9 first (necessary-knowledge priority), then V7 symmetric on the restriction, then reposition the apologetic arguments as legitimate remedial paths |
| NS-8 Muslim-internal crisis | Compound of authority-fatigue + moral recoil + textual-historical / taʿāruḍ pressure presented simultaneously | Compound; often shubhah covering hawā or gharaḍ | P6 / mixed-case-handling first; disaggregate; then matched sub-move per component (taʿāruḍ resolution / M3 / institutional-vs-doctrinal separation) |
| NS-9 Historical-Critical Skeptic | Tawātur flattened; qirāʾāt read as Western text-critical variants; NT transmission conditions imported onto the Qurʾān; method-neutrality held as basic | i'tiqadat mawrutha; often zann | V2 on the imported framework, V10 (separate artifact from authenticated transmission), then `case-library/revelation-transmission.md` for RT-1/2/3 |
| NS-10 Māturīdī Evidentialist | Fiṭrah acknowledged as inclined toward God but demoted from ḍarūrī to preparatory; naẓar required to complete warrant rather than replace fiṭrī recognition | i'tiqadat mawrutha; sometimes zann | `diagnostics/kalamic-interlocutor.md` (Māturīdī section), then V9 (necessary-knowledge priority) |
| NS-11 Fideist / Reformed Basic-Belief | Theist; basic belief affirmed but grounded in proper-function (Plantinga) rather than fiṭrah specifically; no inferential justification required or demanded | Minimal; i'tiqadat mawrutha at philosophical-apparatus level if Reformed epistemology is the only recognized framework | R3 (warranted basic belief), then V5 (directing attention to signs) |
| NS-12 Blank-Slate or Dual-Nature Fiṭrah | Fiṭrah acknowledged as real faculty but disputed as to content; blank-slate (capacity for religiosity, not theism) or dual-nature (equal inclinations toward belief and unbelief) | iʿtiqādāt mawrūtha; sometimes ẓann | `diagnostics/fitrah-perspectives.md`; V5 (phenomenological signs — primary); E4 (cross-cultural check — secondary) |

## Specialty Diagnostic Markers

| Surface marker | Load |
|----------------|------|
| `dalil` demand ("give me a proof/argument"); taqlīd equated with non-knowledge; "naẓar is obligatory on every rational person"; Maturidi concession language | `diagnostics/kalamic-interlocutor.md` |
| Fiṭrah described as blank-slate or purely environment-shaped; "humans have equal tendencies toward good and evil"; religious belief framed as "just one option among equally valid alternatives" | `diagnostics/fitrah-perspectives.md` |
| Historical criticism; manuscript reconstruction; original-text skepticism; "the original text is lost"; "who chose scripture?" | `case-library/revelation-transmission.md` via V10, then RT-1 or RT-2 according to whether the live issue is reconstruction or canon |
| Ḥadīth corpus rejection; isnād / jarḥ wa taʿdīl criticism; āḥād-vs-mutawātir or grading rhetoric | `diagnostics/hadith-authentication-epistemology.md` via V10, then matched doctrine only after the ḥadīth burden is typed |
| Trinity model-identification pressure; perfect-being-to-Trinity argument; incarnation coherence; philosopher's-God challenge | `case-library/do-christian-extensions.md` via V8, then DO-11, DO-12, or DO-13 according to the live issue |
| `ʿilm ḍarūrī` / fiṭrī intuition / necessary knowledge is attacked; "common sense can be wrong"; discursive reasoning is treated as superior to immediate certainty | `references/techniques/V9-necessary-knowledge-priority.md` |
| One premise keeps regenerating the conclusions even after local objections are answered | `diagnostics/seven-deformations.md` §1-A (`mushābara fāsida`) |

## Quick DO Identification

| Code | Objection | Key move | Common confusion |
|------|-----------|----------|-----------------|
| DO-1 | Divine hiddenness | Seven deformations plus P4 | Treating hiddenness as if sincerity alone settled it |
| DO-2 | Evidential evil | M2; M4 if grief-primary | Confusing protest with probability |
| DO-3 | Evolutionary debunking | M1 plus God-through-secondary-causes | Treating genealogy as falsification |
| DO-4 | Religious diversity | Foundation/superstructure distinction | Confusing diversity of expression with diversity of fiṭrī foundation |
| DO-5 | Transcendence and language | V8; analogical predication | Collapsing mystery into contradiction or silence |
| DO-6 | Attribute coherence | V8; dhat/fi'l distinction | Letting philosopher's-God assumptions set the frame |
| DO-7 | Cognitive science of religion / HADD | M1 or V9 depending on form | Accepting a targeted defeater without checking its own criteria |
| DO-8 | Prophetic mission and moral luck | Hujjah principle | Collapsing unequal exposure into divine injustice |
| DO-9 | Great Pumpkin | Universality condition and tawātur fiṭrī | Treating any basic belief as equal to a universal deliverable |
| DO-10 | Three-tiered epistemological structure; attacks on `ʿilm ḍarūrī` / fiṭrī intuition | Fiṭrah -> khabar -> naẓar ordering; V9 when necessary knowledge itself is being denied | Flattening all knowledge into a single inferential tier |
| DO-11 | Trinity from divine perfection; perfect-being-to-Trinity arguments | Distinguish perfection from one mode of exercise | Smuggling revelation-level claims into bare perfection reasoning |
| DO-12 | Logical problem of the Trinity; model-identification pressure | Identify the model first | Letting "mystery" stand in for coherence |
| DO-13 | Philosopher's God vs. God of revelation; incarnation coherence / imported-perfection collapse | Refuse the imported-perfection collapse | Treating abstraction as purification |
| DO-14 | Christian canon selection / authorization pressure | V10 Step 3 canon-authority form, then DO-10 Tier 2 | Collapsing Christian canon-selection into RT-2 or generic diversity |
| DO-15 | Islamic-specific moral objections / imported-criterion form | FPD plus Type D usurpation, then V2 and the internal moral-standard distinction | Conceding a foreign moral tribunal or answering with apology before criterion restoration |

## Quick RT Identification

| Code | Objection | Key move | Common confusion |
|------|-----------|----------|-----------------|
| RT-1 | Viral manuscript / fragment / citation overturns everything | Separate artifact from authenticated transmission with V10 | Treating visual or ancient material as self-authenticating |
| RT-2 | Canon formation destabilizes revelation | Separate canon recognition from inspired authority | Treating list-formation as identical to revelation-status |
| RT-3 | Qur'anic preservation fails because of qirāʾāt / aḥruf / manuscripts | Separate reading categories before drawing corruption claims | Treating recitational plurality as uncontrolled textual collapse |
| RT-4 | Believer destabilized by text-history pressure | Distinguish text-history confusion from authority fatigue and panic | Answering an internal crisis as if it were only a debate prompt |

Ḥadīth corpus/authentication pressures route through
`references/diagnostics/hadith-authentication-epistemology.md` after V10. They remain
outside the RT code family unless a separate RT-1..RT-4 issue is also live.
