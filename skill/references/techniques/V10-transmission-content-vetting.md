---
id: V10-transmission-content-vetting
module_class: technique
canonical_path: skill/references/techniques/V10-transmission-content-vetting.md
contract_version: "0.2.3.0"
load_when:
  - case turns on revelation, scripture, testimony, textual preservation, canon formation, manuscript claims, or viral source allegations
blocks:
  - when live issue is generic theism rather than transmission or authority
  - when live issue is grief-primary protest using text-history as vehicle
  - when live issue is attribute language rather than testimony
  - starting with contents while provenance is still undefined
routing_effects:
  - fixes provenance → contents → authority sequence before any response
  - holds content dispatch until each step cleared
emits:
  - what_is_withheld_and_why
companions:
  - revelation-transmission
  - hadith-authentication-epistemology
  - do-christian-extensions
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-governed
catalogue_registered: true
---

# V10 - Transmission / Content Vetting

Use this technique when the pressure is not merely "is this claim persuasive?" but "what is this
thing, how did it reach us, and what authority does it actually carry?" The sequence is fixed.
Do not begin with contents while provenance is still undefined.

V10 is a selective recursive operator. Each step may clear one burden without licensing a
content dump. After provenance, contents, or authority has been clarified, refresh the
case-state. If another live burden now governs, route there. If not, release only the
smallest restorative next move. Bounded deployment governs the sequence; it does not abolish
further rounds when refreshed state still requires them.

This technique operationalizes a fixed transmission / contents split: first ask how the item
reached us, then ask what it actually shows. Historical criticism, manuscript reconstruction,
canon formation, and original-text skepticism all sit on this split.

## Sequence

### 1. Provenance / transmission check first

Ask what kind of object is actually being presented.

- Is this authenticated transmission, an attributed report, a manuscript witness, an anonymous
  image, a secondary quotation, a historical-critical reconstruction, or a modern skepticism
  about an original text?
- Who is transmitting it, through what path, and with what identifiable chain of custody?
- Is the claim about what a source says, or about whether the source itself is authoritative?

Operational rule:

- Authenticated transmission and anonymous artifacts are not interchangeable.
- A manuscript, screenshot, or citation fragment is not self-authenticating merely because it is
  old, visual, or rhetorically dramatic.
- A late quotation about an earlier source does not by itself become an earlier source.

If provenance is weak, mark that weakness before discussing contents. A text can be interesting
historically while remaining weak as authority.

### 2. Contents check second

Once the object-type is clear, assess what the contents do and do not show.

- Does the text actually say what the claim says it says?
- Are textual variation, manuscript loss, canon formation, qirāʾāt, aḥruf, or interpretive
  dispute being collapsed into one bucket?
- Is the objection really about historical criticism, manuscript reconstruction, canon formation,
  or original-text skepticism rather than about the contents of a settled source?
- Is the objection about reconstruction, preservation, authority, meaning, or doctrine?
- Are analogies crossing traditions without regard to differences in transmission structure?

Operational rule:

- Contents cannot rescue absent provenance.
- Provenance alone does not settle meaning, scope, or doctrinal consequence.
- Distinguish textual data from the theory being imposed on the textual data.

### 3. Authority / shareability decision third

Only after provenance and contents are separated decide how the material may be used.

- Normative authority: what can be treated as binding or reliably transmissible
- Historical witness: what may illuminate a history without becoming doctrinally decisive
- Rhetorical noise: what should not be centered because the basis is too thin

This step governs shareability. Do not circulate a dramatic claim as though it were settled when
it has not passed the first two checks.

**Recognition vs. creation principle (cross-traditional):** A body that recognizes a text's canonical authority is identifying a prior fact about authority — it is not manufacturing new authority by the act of naming. The authority precedes and grounds the recognition; the recognition event does not create it. Conflating recognition with creation is the move that transfers authority from the text's divine source to the human community that named it. This error has the same logical form regardless of tradition: the recognizing body cannot authorize the canon using the canon as its warrant, nor ground its own authority from within the system it is authorizing.

**Canon-authority structural form (cross-traditional):** When the live authority question concerns which texts belong to a canon and why that selection carries binding force — what DO-14 calls sub-question (c) — Step 3 instantiates as: *by what criterion is this selection certified as authoritative, and is that criterion self-grounding?* The criterion-circularity structure is shared across traditions, though the corpora, formation events, and doctrinal objects differ:

- *Protestant sola scriptura* requires a non-scriptural criterion for identifying what counts as Scripture — on pain of circularity.
- *Catholic Magisterium* grounds canonical authority in the Church's teaching authority — which requires independent grounding not derivable from the canon itself.
- *Jewish Masoretic canon* relies on rabbinic recognition; the authority of that recognition requires independent grounding not internal to the rabbinic tradition.
- *Hindu śruti/smṛti hierarchy* rests on Vedic apauruṣeya (non-human-origin) status; establishing that classification for specific texts requires a non-circular criterion.

The tradition-specific corpora, formation events, and arguments differ; the logical form of the criterion problem does not. For the Christian canon-selection and authorization case specifically, see DO-14 (sub-question (c) and the authorization analysis), which is this file's Christian-instance. Route from DO-14 sub-question (c) → DO-10 Tier 2 for the positive Islamic epistemological account.

**People-of-the-Book prooftext discipline:** When Torah, Injil, rabbinic, or biblical
material appears in a final-prophethood, canon, or authority case, classify the move
before using any text:

- Qur'an-grounded report about prior revelation
- current-text corroboration
- argument from an interlocutor-granted canon
- internal inconsistency refutation
- unsupported apologetic prooftexting

Do not make external scriptures a clean independent foundation before provenance,
contents, authority, translation, canon, and interpretive standing have been typed.
If the live pressure is closed-canon veto or selective scriptural arbitrage, route
authority order first; prooftexts are held until source-use discipline clears.

## Tradition-Specific Branch Operators

After the three-step sequence, route to the appropriate branch. Each branch specifies what changes in the sequence and what conflations are prohibited within it. Do not apply one branch's constraints to another — the traditions have structurally different transmission architectures.

### Branch A — Qurʾān: Qirāʾāt, Aḥruf, Manuscript Plurality

**What changes in the sequence:** Provenance for the Qurʾān is established through the concept of tawātur — mass independent transmission across chains rather than chain-of-custody for a single document. The question at Step 1 is not "what manuscript is this?" but "has this reading been transmitted through a mutawātir channel or not?" Variants classified as tawātur lafẓī (verbatim mass transmission) and qirāʾāt (approved readings transmitted through named chains with multiple independent attestation) are not evidence of corruption — they are the expected texture of the transmission system.

**Prohibited conflations:**
- Do not treat qirāʾāt plurality as equivalent to uncontrolled textual corruption. Qirāʾāt are not manuscript variants in the sense of accidental divergence; they are licensed readings transmitted through named chains.
- Do not treat the existence of early manuscripts (Ṣanʿāʾ, Topkapi) as independent transmission evidence in the sense that contradicts the oral transmission structure. The manuscript tradition is secondary in function; the primary transmission vehicle is oral.
- Do not treat aḥruf (the seven modes of revelation) as equivalent to seven independently authored texts.
- Do not collapse the distinction between what is mutawātir (certain) and what is āḥād (probable) in transmission status.

**Route after:** RT-3 for qirāʾāt/aḥruf/manuscript cases; RT-4 if a Muslim is destabilized by material about Qurʾānic text history.

---

### Branch B — Biblical Canon and Manuscripts

**What changes in the sequence:** The Biblical transmission system does not rest on mutawātir oral transmission as a primary vehicle. The provenance question (Step 1) centers on: which manuscript tradition, through which textual family, with what degree of attestation, and at what proximity to the claimed original? Canon formation (what was included and when) is a distinct question from textual transmission (how reliably a text was copied). These must not be collapsed.

**Prohibited conflations:**
- Do not treat "many early manuscripts agree" as equivalent to the Islamic tawātur standard — the attestation structures are different in kind, not only in degree.
- Do not treat canon formation debates as establishing that no scriptures are reliable — the scope of the canon question is different from the reliability of particular texts within it.
- Do not treat later manuscript discovery (Dead Sea Scrolls, Oxyrhynchus papyri) as automatically overturning later canonical text — the relationship between earlier and later manuscripts requires text-critical methodology, not a simple "earlier is more authentic" rule.
- Do not let the interlocutor conflate "the Bible has textual variants" (true of all ancient documents) with "the Bible has been substantially corrupted from its original" (a strong claim requiring substantive argument).

**Route after:** RT-2 for Islamic canon-formation pressure; DO-14 for Christian canon-selection and authorization questions (sub-questions (a)–(c)); RT-1 for specific viral manuscript or fragment claims.

---

### Branch C — Ḥadīth, Isnād, and Wijādah

**What changes in the sequence:** Ḥadīth transmission operates through isnād (chains of narrators) with an elaborate classification science. The provenance question (Step 1) must determine: the classification of the report (ṣaḥīḥ, ḥasan, ḍaʿīf, mawḍūʿ), which collection it appears in, and whether the critique being pressed targets a specific report or the ḥadīth system as such. These are entirely different problems requiring different responses.

**Prohibited conflations:**
- Do not treat a ḍaʿīf (weak) report as having the same evidential weight as a ṣaḥīḥ (sound) one. The classification is not decorative — it determines the epistemic status of the transmission.
- Do not treat late compilation of collections (Bukhārī d. 870 CE) as evidence that the reports were invented at that date. The transmission chains predate the collection; the date of the collection is the date of final written organization, not of the transmitted content.
- Do not let wijādah (found-document transmission without a live isnād) be treated as normative — it has a lower epistemic status than mutawātir or ṣaḥīḥ isnād transmission.
- Do not collapse the distinct questions: was this specific ḥadīth reliably transmitted? vs. is the ḥadīth system as a whole a reliable transmission mechanism?

**Route after:** `references/diagnostics/hadith-authentication-epistemology.md` for burden typing and release discipline. Do not route straight to RT-1 or to a DO file. Downstream doctrinal files load only after the ḥadīth owner has stated whether the live pressure is corpus, method, report-class / epistemic-yield, or grade confusion.

---

### Branch D — Final Prophethood: Transmission and Doctrine Intertwined

**What changes in the sequence:** Final-prophethood cases present a unique intertwining: the doctrinal claim (Muḥammad ﷺ is the seal of the prophets) is itself partially a transmission claim (the Qurʾān transmits this; the ḥadīth tradition transmits this; the community transmits this continuously). The objection may target the transmission (was this reliably transmitted?) or the doctrine (does this make sense as a divine arrangement?) or both at once.

The three-step sequence must be run on each layer separately: What is the transmission status of the specific verses, reports, or claims being pressed? What do the contents of the properly vetted material actually show? What authority does that material carry for the specific doctrinal question?

**Prohibited conflations:**
- Do not let a transmission challenge to the seal-of-prophets doctrine collapse into a general "the Qurʾān might be unreliable" argument without the interlocutor establishing that the specific transmission mechanism for those specific texts has failed.
- Do not let a theological objection ("why would God stop sending prophets?") be treated as if it were a transmission objection — the registers require different instruments.
- Do not treat an argument about the timing or necessity of final prophethood as equivalent to an argument about whether the transmission of the claim is sound. These are orthogonal questions.

**Route after:** DO-series for purely doctrinal challenges after transmission is cleared; RT-1 or RT-3 if specific text-transmission questions are live.

---

## Matched Uses

For recurring family treatments after this sequence, see
`references/case-library/revelation-transmission.md`.

- Viral manuscript or screenshot claims -> start here, then route to RT-1
- Historical criticism / original-text skepticism -> start here, then route to RT-1 if the live
  issue is manuscript reconstruction, or RT-2 if the live issue is canon formation
- Canon-formation pressure or "who chose scripture?" -> start here, then route to RT-2
- Qur'anic preservation / qirāʾāt / manuscript confusion -> start here, then route to RT-3
- Ḥadīth corpus rejection / isnād criticism / āḥād-vs-mutawātir / grade-confusion pressure -> start here, then route to `diagnostics/hadith-authentication-epistemology.md`
- Muslim-internal panic over text-history material -> start here, then route to RT-4
- Final-prophethood challenges entangled with text-history or testimony -> use here before broader
  prophetic-credibility rebuttal

## Do Not Use When

- The live issue is whether God exists at all rather than whether a transmission claim is sound
- The case is grief-primary or betrayal-primary and text-history is only a vehicle
- The objection is really about divine attributes, evil, or hiddenness rather than testimony

## Common Confusions

- Treating "old manuscript" as equivalent to authenticated transmission
- Treating canon formation as equivalent to inspired authority
- Treating qirāʾāt differences as equivalent to uncontrolled textual corruption
- Treating a destabilized believer as though they were posing a neutral historical question

If provenance remains unclear, say so plainly and stop short of doctrinal overreach.
