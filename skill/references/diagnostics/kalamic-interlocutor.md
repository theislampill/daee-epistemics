> role: specialty diagnostic — kalāmic evidentialism engagement strategy (Muʿtazilī / Ashʿarī / Māturīdī variants)
> use when: NS-6 or NS-10 confirmed; surface markers of kalāmic evidentialism present (dalīl demand, wujūb al-naẓar, taqlīd-as-non-knowledge, fiṭrah denied epistemic weight without propositional support)
> do not use when: interlocutor is externalist-secular (NS-1/NS-2) and does not operate within a kalāmic theological framework
> section-to-NS mapping:
>   §Surface Recognition Markers + §The Kalāmic Position + §The Critique + §Engaging the Kalāmic Interlocutor → NS-6 primary; also load for NS-10 (shared infrastructure)
>   §The Māturīdī Position — Distinct Engagement Path → NS-10 primary; do not load for NS-6 cases where Māturīdī softening is not the live form
>   §The Ontological Dimension → load when the kalāmic interlocutor's position is about divine attributes, not merely the epistemological framework
> load-discipline: load the whole file; use only the section(s) matched to the confirmed school variant and live pressure
> paired files: NS-6 profile (case-library/profiles/ns-6-kalamic-evidentialist.md); NS-10 profile (case-library/profiles/ns-10-maturidi-evidentialist.md); V2 (reconstituting reason); P3 (reason-revelation tension); V9 (necessary-knowledge priority for Māturīdī section)

# Kalāmic Interlocutor — Engagement Strategy

Load when the interlocutor uses surface markers of kalāmic evidentialism: theistic belief
must be grounded in `dalil`; `wujūb al-naẓar` is assumed or defended; taqlīd-based belief is
treated as non-knowledge; the fiṭrah alone is denied epistemic weight without propositional
support; Māturīdī concession language is surfacing; or the interlocutor explicitly identifies with
Muʿtazilī, Ashʿarī, or Māturīdī reasoning.

---

## Downstream Routing Table — School × Burden

School identification is not optional. Once this file is loaded, the school variant must be
identified before restoration target and matched modules are committed to the IR. Do not
dispatch NS-6 with a generic "foundationalist restriction" restoration target without first
running the identification step below. The table governs what changes downstream.

**Burden identification rule:**
- **Epistemological burden:** the live pressure is wujūb al-naẓar, taqlīd-as-non-knowledge,
  or the narrow necessary-knowledge restriction — regardless of what doctrinal object is named.
- **Ontological burden:** the live pressure is divine attributes, divine speech, the status of
  the Qurʾān, or any claim governed by the ḥudūth/khalq distinction or kalām nafsī doctrine.
- **Mixed:** both are simultaneously live. Sequence epistemological first; ontological second.
  Do not flatten into a single "kalāmic engagement" — the targets and load conditions differ.

| School variant | NS code | Burden | Restoration target | Must load (beyond this file) | Prohibited moves |
|---------------|---------|--------|--------------------|------------------------------|------------------|
| Muʿtazilī | NS-6 | Epistemological | Expose the self-undermining circularity: wujūb al-naẓar presupposes the fiṭrī reliability it demotes; naẓar cannot certify itself from nowhere | V2 (inherited filter); backbone predicates T-2, T-3 | Do not engage the hard wujūb as merely "too strict" — it is structurally self-undermining; do not concede fiṭrī recognition as sub-epistemic without argument |
| Muʿtazilī | NS-6 | Ontological | Deploy the ḥudūth/khalq distinction explicitly: the Muʿtazilī inferred makhlūq from ḥudūth — name and dissolve this collapse; §6.2 is the required grounding | §6.2 of `sound-reason-epistemology.md` + V8 + `terminology.md` (Khalq, Ṣifa qāʾima bi-dhātihi); `do-attribute-precision.md` Confusion 1 (Muʿtazilī predication move) | Do not leave the ḥudūth premise standing as a concession; the ḥudūth/khalq distinction is the load-bearing move — ḥādith ≠ makhlūq |
| Ashʿarī | NS-6 | Epistemological | Press the communal-obligation softening toward its structural crack: if ordinary believers need not individually demonstrate, their belief is already non-inferentially warranted — name the concession | V2; the naẓar-circularity argument | Do not treat Ashʿarī softening as movement toward the sound position; it retains the inferential framework while relocating the obligation — the framework error is not resolved by communal-level transfer |
| Ashʿarī | NS-6 | Ontological | Target the kalām nafsī doctrine specifically: it severs the expressed Qurʾān from being genuinely God's speech in the sense the texts require — not merely philosophically awkward, but a textual-theological failure; deploy §6.2 three-way differentiation | §6.2 + V8 + `terminology.md` (Ṣifa qāʾima bi-dhātihi); `do-attribute-precision.md` | Do not allow the kalām nafsī doctrine to remain standing while engaging bilā kayf generally; it is a named Ashʿarī error, not a legitimate bilā kayf position; bilā kayf is the correct position, kalām nafsī is a deviation from it |
| Māturīdī | NS-10 | Epistemological | Press the internal instability: the communal-obligation concession already breaks the individual requirement — name what has been conceded; the admission of non-propositional evidence already opens the inferential framework | V9 (necessary-knowledge priority); §Māturīdī section in this file | Do not endorse the communal-obligation move as correct; it is a pressure point exposing instability, not a halfway house; do not treat the Māturīdī position as a valid intermediate |
| Māturīdī | NS-10 | Ontological | Shared Ashʿarī Kullābī inheritance: engage as diagnosed Ashʿarī ontological error — the restoration target is the same as Ashʿarī ontological | §6.2 + V8 | Do not treat Māturīdī ontological position as a distinct third pole; at the ontological level it inherits the Ashʿarī error |
| School unclear (provisional) | NS-6 provisional | Epistemological | Hold provisional read; deploy naẓar-circularity argument as school-neutral opening while identification runs | V2; this file's §The Critique | Do not commit to a school-specific restoration target or prohibited move before the identification differentiator is in |
| Mixed (any school) | NS-6 or NS-10 | Epistemological + Ontological | Sequence: address epistemological burden (foundationalist restriction) first; ontological burden second (school-specific target per above) | Per school row above for each burden; both must load | Do not flatten both burdens into a single "kalāmic engagement" — they have different restoration targets and the wrong sequence inverts the repair order |

---

## Surface Recognition Markers

The following are sentence patterns, objection forms, and terms of approval or dismissal a
practitioner would actually hear from an interlocutor formed in the kalāmic framework. Each
is derived from the doctrinal content described in this file.

1. **Dalīl demand:** "You need to give me a proof (dalīl) — your belief doesn't count as
   knowledge unless it is grounded in an argument." Variations: "Show me the evidence,"
   "What is your proof for that?" — where the demand is specifically for *propositional*
   demonstration rather than any other epistemic ground.

2. **Taqlīd dismissal:** "That is just taqlīd — you only believe because your parents did.
   Taqlīd is not knowledge; every rational person must investigate for themselves." The
   key signal is the equation of inherited or unarticulated belief with non-knowledge
   rather than merely with *unexamined* belief.

3. **Wujūb al-naẓar assertion:** "Rational inquiry (naẓar) is obligatory on every sane
   adult — there is no valid excuse for not reasoning your way to the answer." The
   obligation framing is the marker: not merely that reasoning is useful but that it is
   *required* before belief can have epistemic standing.

4. **Dismissal of fiṭrah-alone as insufficient:** "Feeling it, or being inclined toward
   it, doesn't make it knowledge. The fiṭrah is not an argument." The practitioner will
   hear this as a flat rejection of non-inferential grounds — the fiṭrah is acknowledged
   as a psychological fact but denied epistemic weight without propositional support.

5. **Narrow-foundations restriction:** "Sense perception and logical self-evidence give
   you knowledge — everything else needs to be demonstrated." Or: "That kind of immediate
   certainty only applies to mathematics and direct observation." This pattern restricts
   properly basic beliefs to the kalāmic ḍarūrī class and treats everything outside it
   as needing inferential grounding.

6. **Approval of demonstration, dismissal of recognition:** Terms of praise cluster around
   propositional success — "That is a proper proof," "Now you have established it," "That
   argument holds." Terms of dismissal cluster around directness and recognition — "That
   is just intuition," "You are assuming what you need to prove," "That is circular." The
   asymmetry itself is the marker: direct recognition counts as nothing; successful
   inference counts as knowledge.

7. **Māturīdī concession language:** "The ordinary believer may rely on the community's
   demonstration," "the obligation may be communal rather than individual," or "miracle,
   Qur'anic encounter, or experience can still ground valid faith." The signal here is not
   hard evidentialism but a softened inferential framework retaining the vocabulary of
   obligation and ratification.

---

## The Kalāmic Position

The major schools of kalām share a foundationalist epistemology that restricts necessary
knowledge (ʿilm ḍarūrī) to: logical axioms, sense perceptions, incorrigible beliefs,
and mutawātir testimony. Theistic belief falls outside this class. Therefore, for
religious belief to achieve the status of knowledge, it must be based on propositional
evidence (dalīl). This generates the doctrine of wujūb al-naẓar: the obligation on
every rational person to engage in discursive rational inquiry as the means to knowledge
of God.

**Consequences:**
- Belief held without argument cannot achieve the status of knowledge — only taqlīd
- The Muʿtazila hold such taqlīd-based belief to be epistemically and morally
  impermissible
- The Ashʿarī tradition softens this to a communal rather than individual obligation
  but retains the inferential requirement
- In all versions: theistic belief grounded in the fiṭrah alone, without propositional
  support, fails to achieve knowledge

## The Critique

**First — the foundationalist restriction is arbitrarily narrow:** The kalāmic framework
restricts properly basic beliefs to a narrow class without principled justification.
Why should belief in other minds, in the reliability of memory, in the past — none of
which pass the kalāmic ḍarūrī tests — be epistemically acceptable, while theistic
belief held with the same immediacy and involuntariness is not? The criterion is applied
selectively. The restriction imports a historically contingent model of non-inferential
knowledge that is itself not self-evident.

**Second — the fiṭrah widens the foundations legitimately:** Fiṭrī-ḍarūrī knowledge
extends the class of properly basic beliefs beyond what the kalāmic framework recognizes.
The fiṭrah produces warranted belief in God directly, without inference, when functioning
without corruption. This is not a retreat from epistemic rigor — it is a more accurate
account of how belief-warrant works, one that the externalist faculty-based epistemology
of the Reidian tradition later converged on independently.

**Third — the circularity of wujūb al-naẓar:** The obligation to engage in naẓar
presupposes the reliability of naẓar as a cognitive procedure. But what grounds the
reliability of naẓar? The fiṭrah — "the proper functioning of all our epistemic
faculties is predicated on the health and proper functioning of the fiṭrah." Naẓar not
grounded in sound fiṭrah is contaminated rationality (bidʿī ʿaqlī) that feels like pure
reason but is not. The kalāmic framework depends on the very thing it undervalues.

**Fourth — misrepresentation of the prophetic method:** No prophet addressed his
community by demanding they first master rational proofs before any religious knowledge
was valid. The prophets directed attention to signs (āyāt) — already present in creation
and in the soul — and invited recognition, not demonstration. The kalāmic demand for
inferential grounding inverts the actual epistemological structure of prophetic
communication.

## Engaging the Kalāmic Interlocutor

The engagement operates on two levels simultaneously:

**1. Internal Islamic ground:** The framework grounded in ʿaql ṣarīḥ and naql ṣaḥīḥ is
not a position competing with the kalāmic schools for legitimacy — it is the sound
Islamic epistemology, the one that correctly accounts for the prophetic method and is
faithful to the Qurʾānic account of how human beings come to know God. The kalāmic schools
deviated from this through the importation of Hellenistic categories; this is a diagnosis,
not a preference. The engagement shows the kalāmic framework as what it is — a historically
contingent deviation — and returns the interlocutor to what sound reason and authentic
revelation have always held.

**2. The specific mechanism of deviation:** The kalāmic framework imported bidʿī ʿaqlī
(contaminated rationality) and presented it as reason itself. Genuine reason (ʿaql ṣarīḥ)
always agrees with genuine revelation (naql ṣaḥīḥ); the kalāmic schools substituted a
Hellenistic-conditioned conception of reason for the real thing, then read revelation
through the resulting distorting filter. The engagement names this mechanism clearly: not
as one theological preference against another, but as the difference between sound reason
and its contaminated substitute.

## The Māturīdī Position — Distinct Engagement Path

The Māturīdī tradition is a distinct deviation, not a legitimate midpoint between the
Muʿtazilī error and the sound position. It softens the Muʿtazilī requirement (wujūb
al-naẓar becomes communal rather than individual; non-propositional evidence is admitted
in some forms), but it retains the inferential framework and its characteristic errors on
divine being. The school's ontological positions — on divine attributes, on the nature of
kalām — are not authoritative; they share the Ashʿarī inheritance of Hellenistic
contamination at the ontological level and produce their own distinct errors at the
epistemological level.

An interlocutor formed in the Māturīdī tradition holds a position that is internally
unstable and can be pressed from within. The engagement path is tactical, not one of
concession:

**Engage the Māturīdī concession as a pressure point — not an endorsement:** The communal
obligation reading already breaks the individual requirement; the allowance of
non-propositional evidence already opens a crack in the inferential framework. Use these
as levers to press the position toward its own inconsistency. This is a tactical move —
working with where the position has already partially collapsed — not an affirmation that
the Māturīdī framework is correct.

**Press the instability of the communal-obligation move:** If the ordinary believer need
not personally argue their way to God, on what basis does their belief have epistemic
standing? If reliance on the community's demonstration is sufficient, the belief's warrant
is grounded in something other than the believer's own inferential process — which is
precisely what the externalist account of the fiṭrah holds. The Māturīdī position has
quietly conceded the externalist point while retaining the vocabulary of obligation. Name
what has been conceded.

**Show the fiṭrah account is the correct one:** The fiṭrah account does not occupy a
position "beyond" the Māturīdī concession by degree — it corrects the Māturīdī framework
at the root. The fiṭrah produces warranted belief directly when functioning correctly; the
scholarly community's arguments serve to restore the fiṭrah's operation when it has been
corrupted, not to supply what the fiṭrah lacks. The Māturīdī framework constructs an
architecture of individual vs. communal obligations precisely because it has already
misconstrued the epistemic structure of prophetic communication.

## The Ontological Dimension — Ashʿarī and Māturīdī Errors on Divine Being

**Load §6.2 of `references/sound-reason-epistemology.md` and the Ḥudūth/Khalq/Ṣifa qāʾima
bi-dhātihi entries in `references/terminology.md` when the kalāmic interlocutor's position
is about divine attributes, divine speech, or the status of the Qurʾān — not merely about
the epistemological framework.**

The kalāmic files' epistemological errors (wujūb al-naẓar, restricted foundationalism) are
well-mapped above. Their **ontological** errors are a separate and equally serious failure:

**Ashʿarī ontological position (diagnosed error):** Following the Ibn Kullāb inheritance,
the Ashʿarī school denied that any ḥawādith (temporally originating events) could subsist
in God, on the grounds that this would entail the succession of temporal events in the
divine being (taʿāqub al-ḥawādith ʿalayhi). The result was the doctrine of kalām nafsī —
an eternal inner meaning attributed to God as the "true" divine speech — while the verbally
expressed Qurʾān (its ḥurūf and aṣwāt) was held to be created but external. This is a
deviation from the sound position on two counts: it denies the subsistence of volitional
acts in the divine essence (al-umūr al-ikhtiyāriyya al-qāʾima bi-dhātihi), and it produces
a doctrine of divine speech that severs the revealed Qurʾān from being genuinely God's own
word in the sense the texts require. This deviation — a remnant of Muʿtazilī principles
embedded in Ashʿarism — worsened with each successive generation.

**Muʿtazilī ontological position (diagnosed error):** Denied the hypostatic character of
the essential attributes entirely; treated ḥudūth (temporal origination) as sufficient for
khalq (external creation), collapsing the ḥudūth/khalq distinction that the sound position
depends on. The consequence was the createdness of the Qurʾān as an external object — the
most notorious deviation.

**Governing principle:** The kalāmic schools' ontological positions are not treated as valid
Islamic alternatives. They are diagnosed as historically arising from the importation of
Hellenistic categories into Islamic theology — categories that were never validated by ʿaql
ṣarīḥ or naql ṣaḥīḥ and that systematically distorted the account of divine being. When
engaging a kalāmic interlocutor on divine attributes, confirm the ḥudūth/khalq distinction
is in the response (V8 routing check) and engage their ontological position as a diagnosed
error, not as a competing school with equal standing.
