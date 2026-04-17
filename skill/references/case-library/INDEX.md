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
| NS-1 through NS-6 | `case-library/noetic-profiles.md` | You only have a topic, not a recognizable noetic type | V1, M5, V2, M3 |
| DO-1 through DO-6 | `case-library/do-core.md` | The objection family is not yet distinguished from grief, criterion protest, or testimony critique | M2, V8, P2 |
| DO-7 through DO-10 | `case-library/do-second-loop.md` | The case is still at first-order objection level | M1, V9, P2 |
| DO-11 through DO-13 | `case-library/do-christian-extensions.md` | Trinity or philosopher's-God pressure has not been classified precisely | V8, P2 |
| RT-1 through RT-4 | `case-library/revelation-transmission.md` | The case has not yet been separated into testimony, text, canon, prophetic-claim, or believer-destabilization layers | V10, P2, P5 |

## Quick NS Identification

| Profile | Marker | Primary deformation | First likely move |
|---------|--------|---------------------|------------------|
| NS-1 Naturalist | "there is no evidence"; causal closure assumed; drift toward sophistic skepticism under consistent pressure | I'tiqadat mawrutha | V2 |
| NS-2 Agnostic Evidentialist | "belief must be proportioned to evidence"; refusal of non-inferential warrant | zann; possibly genuine shubha | E2 plus V3 |
| NS-3 Deconverted | Grievance-stabilized argumentation around a single shubhah; orphaned moral commitments | hawa; zann; possibly gharad | M3 or P4 |
| NS-4 Secular Moral Realist | Moral facts are objective but God is rejected; normativity helped-to without ontology | zann; i'tiqadat mawrutha | M3 |
| NS-5 Habituated Atheist | God's non-existence treated as basic | Primarily hawa; possibly gharad; 'ada | F2 (volitional acknowledgment) first; then M4 if grief-primary, R2 if involuntary recognition near surface, V7 otherwise |
| NS-6 Kalamic Evidentialist | `dalil` demand; `wujub al-nazar`; taqlid treated as non-knowledge; narrow necessary-knowledge class | i'tiqadat mawrutha; often zann | `diagnostics/kalamic-interlocutor.md`, then V2 or P3 as the live conflict requires |
| NS-7 Theistic Evidentialist | God affirmed; natural-theology apparatus held as the *precondition* for warranted belief; fiṭrī recognition demoted to "mere feeling" | i'tiqadat mawrutha; often zann | V9 first (necessary-knowledge priority), then V7 symmetric on the restriction, then reposition the apologetic arguments as legitimate remedial paths |
| NS-8 Muslim-internal crisis | Compound of authority-fatigue + moral recoil + textual-historical / taʿāruḍ pressure presented simultaneously | Compound; often shubha covering hawa or gharad | P6 / mixed-case-handling first; disaggregate; then matched sub-move per component (Darʾ taʿāruḍ / M3 / institutional-vs-doctrinal separation) |
| NS-9 Historical-Critical Skeptic | Tawātur flattened; qirāʾāt read as Western text-critical variants; NT transmission conditions imported onto the Qurʾān; method-neutrality held as basic | i'tiqadat mawrutha; often zann | V2 on the imported framework, V10 (separate artifact from authenticated transmission), then `case-library/revelation-transmission.md` for RT-1/2/3 |

## Specialty Diagnostic Markers

| Surface marker | Load |
|----------------|------|
| `dalil` demand ("give me a proof/argument"); taqlīd equated with non-knowledge; "naẓar is obligatory on every rational person"; Maturidi concession language | `diagnostics/kalamic-interlocutor.md` |
| Fiṭrah described as blank-slate or purely environment-shaped; "humans have equal tendencies toward good and evil"; religious belief framed as "just one option among equally valid alternatives" | `diagnostics/fitrah-perspectives.md` |
| Historical criticism; manuscript reconstruction; original-text skepticism; "the original text is lost"; "who chose scripture?" | `case-library/revelation-transmission.md` via V10, then RT-1 or RT-2 according to whether the live issue is reconstruction or canon |
| Trinity model-identification pressure; perfect-being-to-Trinity argument; incarnation coherence; philosopher's-God challenge | `case-library/do-christian-extensions.md` via V8, then DO-11, DO-12, or DO-13 according to the live issue |
| `ilm daruri` / fitri intuition / necessary knowledge is attacked; "common sense can be wrong"; discursive reasoning is treated as superior to immediate certainty | `references/techniques/V9-necessary-knowledge-priority.md` |
| One premise keeps regenerating the conclusions even after local objections are answered | `diagnostics/seven-deformations.md` §1-A (`mushābara fāsida`) |

## Quick DO Identification

| Code | Objection | Key move | Common confusion |
|------|-----------|----------|-----------------|
| DO-1 | Divine hiddenness | Seven deformations plus P4 | Treating hiddenness as if sincerity alone settled it |
| DO-2 | Evidential evil | M2; M4 if grief-primary | Confusing protest with probability |
| DO-3 | Evolutionary debunking | M1 plus God-through-secondary-causes | Treating genealogy as falsification |
| DO-4 | Religious diversity | Foundation/superstructure distinction | Confusing diversity of expression with diversity of fitri foundation |
| DO-5 | Transcendence and language | V8; analogical predication | Collapsing mystery into contradiction or silence |
| DO-6 | Attribute coherence | V8; dhat/fi'l distinction | Letting philosopher's-God assumptions set the frame |
| DO-7 | Cognitive science of religion / HADD | M1 or V9 depending on form | Accepting a targeted defeater without checking its own criteria |
| DO-8 | Prophetic mission and moral luck | Hujjah principle | Collapsing unequal exposure into divine injustice |
| DO-9 | Great Pumpkin | Universality condition and tawatur fitri | Treating any basic belief as equal to a universal deliverable |
| DO-10 | Three-tiered epistemological structure; attacks on `ilm daruri` / fitri intuition | Fitrah -> khabar -> nazar ordering; V9 when necessary knowledge itself is being denied | Flattening all knowledge into a single inferential tier |
| DO-11 | Trinity from divine perfection; perfect-being-to-Trinity arguments | Distinguish perfection from one mode of exercise | Smuggling revelation-level claims into bare perfection reasoning |
| DO-12 | Logical problem of the Trinity; model-identification pressure | Identify the model first | Letting "mystery" stand in for coherence |
| DO-13 | Philosopher's God vs. God of revelation; incarnation coherence / static-deity collapse | Refuse the static-deity collapse | Treating abstraction as purification |

## Quick RT Identification

| Code | Objection | Key move | Common confusion |
|------|-----------|----------|-----------------|
| RT-1 | Viral manuscript / fragment / citation overturns everything | Separate artifact from authenticated transmission with V10 | Treating visual or ancient material as self-authenticating |
| RT-2 | Canon formation destabilizes revelation | Separate canon recognition from inspired authority | Treating list-formation as identical to revelation-status |
| RT-3 | Qur'anic preservation fails because of qira'at / ahruf / manuscripts | Separate reading categories before drawing corruption claims | Treating recitational plurality as uncontrolled textual collapse |
| RT-4 | Believer destabilized by text-history pressure | Distinguish text-history confusion from authority fatigue and panic | Answering an internal crisis as if it were only a debate prompt |
