<!--
GENERATED FILE.
Do not edit directly.
Canonical atomized source lives under atomics/skill/.
Regenerate with tools/build_compiled_runtime.py.
-->

# OMNIBUS-profiles

This generated bundle is a runtime read view. Section presence does not imply active dispatch.


## SOURCE MODULE: profiles-index

<!-- SOURCE: atomics/skill/references/case-library/profiles/INDEX.md -->
<!-- MODULE_ID: profiles-index -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/INDEX.md -->
<!-- SOURCE_SHA256: 0796d5291616132cfeec46e9055bac5344bb5685bf5ffb1a8817a192e5cc254e -->

---
id: profiles-index
module_class: governance
canonical_path: skill/references/case-library/profiles/INDEX.md
contract_version: "0.3.0.0"
load_when:
  - NS code identified and canonical profile file location needed
catalogue_registered: false
---

# Noetic Structure Profiles — Directory Index

Each NS profile is individually owned, individually IR-addressable, and never co-loaded with
another profile. Confirm the NS code via `case-library/INDEX.md §Quick NS Identification`, then
load the matched file below. Do not load this index file as a substitute for the profile.

## Routing Table

| NS code | Profile | File |
|---------|---------|------|
| NS-1  | Naturalist | `profiles/ns-1-naturalist.md` |
| NS-2  | Agnostic Evidentialist | `profiles/ns-2-agnostic-evidentialist.md` |
| NS-3  | Deconverted (Post-Religious) | `profiles/ns-3-deconverted.md` |
| NS-4  | Secular Moral Realist | `profiles/ns-4-secular-moral-realist.md` |
| NS-5  | Habituated Atheist | `profiles/ns-5-habituated-atheist.md` |
| NS-6  | Kalāmic Evidentialist | `profiles/ns-6-kalamic-evidentialist.md` |
| NS-7  | Theistic Evidentialist | `profiles/ns-7-theistic-evidentialist.md` |
| NS-8  | Muslim-Internal Crisis (Compound) | `profiles/ns-8-muslim-internal-crisis.md` |
| NS-9  | Historical-Critical Skeptic | `profiles/ns-9-historical-critical-skeptic.md` |
| NS-10 | Māturīdī Evidentialist | `profiles/ns-10-maturidi-evidentialist.md` |
| NS-11 | Fideist / Reformed Basic-Belief | `profiles/ns-11-fideist-reformed.md` |
| NS-12 | Blank-Slate or Dual-Nature Fiṭrah | `profiles/ns-12-blank-slate-dual-fitrah.md` |

## Minimal-Pair Discriminators

### NS-2 (Agnostic Evidentialist) vs. NS-6 (Kalāmic Evidentialist)

*Decision rule:* Both demand inferential argument before granting warrant to theistic belief. The
difference is the framework. NS-2 operates within a broadly empiricist or analytic framework;
NS-6 operates within a kalāmic theological framework that accepts revelation in principle but
requires naẓar (inferential reasoning) as ratificatory.

*Left correct (NS-2):* Interlocutor says "I won't believe in God without sufficient empirical
evidence — the same standard I'd apply to any other claim." No reference to kalāmic vocabulary;
no acceptance of revelation as a legitimate source; the standard is secular-empiricist. Correct
instrument: V2 (contaminated conception of reason) before any evidential content. Not NS-6 — the
framework is not kalāmic.

*Right correct (NS-6):* Interlocutor is a madrasa-trained student who says "taqlīd is not
knowledge — I need to know my ʿaqīdah through naẓar." Accepts the legitimacy of revelation in
principle but treats the kalāmic evidentialist criterion (wujūb al-naẓar) as a requirement for
their own knowledge. V2 still applies, but the contamination is kalāmic, not secular; load
`references/diagnostics/kalamic-interlocutor.md` to locate the specific school position. Not
NS-2 — the framework is already within a theistic tradition.

*Differentiating signal:* Does the interlocutor accept the legitimacy of revelation as a knowledge
source in principle, while nonetheless requiring inferential ratification? If yes, NS-6. If
revelation is itself not accepted as a legitimate source, NS-2.

---

### NS-6 (Kalāmic Evidentialist) vs. NS-10 (Māturīdī Evidentialist)

*Decision rule:* Both operate within the kalāmic tradition. The difference is how the fiṭrah is
positioned. NS-6 treats naẓar as a replacement for fiṭrī knowledge (or as its obligatory
precondition before theistic belief is even licit). NS-10 concedes the fiṭrah's orientation
toward God but demotes its epistemic standing from ḍarūrī to preparatory — naẓar completes rather
than replaces it. Full discriminator in `references/diagnostics/kalamic-interlocutor.md`.

*Sub-variant within NS-6 — Muʿtazilī vs. Ashʿarī:* Once NS-6 is confirmed (not NS-10), the
school must be further identified. Both are "hard kalāmic" (naẓar as obligatory precondition),
but they differ materially when the ontological dimension is live:
- **Muʿtazilī strand:** restoration target on ontological burden = ḥudūth/khalq distinction (the
  Muʿtazilī error was inferring makhlūq from ḥudūth); prohibited move = accepting ḥudūth as a
  concession without dissolving the makhlūq inference.
- **Ashʿarī strand:** restoration target on ontological burden = kalām nafsī doctrine (the Ashʿarī
  error was denying all ḥawādith in God, severing the expressed Qurʾān from genuine divine speech);
  prohibited move = treating the kalām nafsī doctrine as a legitimate bilā kayf position rather
  than a named deviation.
- On epistemological burden only (no divine attributes or speech live), the Muʿtazilī/Ashʿarī
  distinction does not change the primary instrument (V2 + naẓar-circularity argument), though
  the Ashʿarī communal-obligation softening is a distinct pressure point to exploit.
See `diagnostics/kalamic-interlocutor.md` §Downstream Routing Table for the complete
school × burden consequence mapping.

---

### NS-7 (Theistic Evidentialist) vs. NS-11 (Fideist / Reformed Basic-Belief)

*Decision rule:* Both are theists. NS-7 believes but insists the belief must be inferentially
grounded before it counts as knowledge; NS-11 believes and insists it need not be. They require
opposite interventions: NS-7 needs to be loosened from the evidentialist restriction; NS-11 needs
the fiṭrī account placed alongside the proper-function account as a more specific articulation.

---

### NS-1/NS-2 vs. NS-12 (Blank-Slate or Dual-Nature Fiṭrah)

*Decision rule:* NS-1 and NS-2 are externalist — they operate from a secular framework that does
not acknowledge the fiṭrah at all. NS-12 acknowledges the fiṭrah as a genuine human faculty but
disputes its content (blank-slate: no determinate theistic content; dual-nature: equal pulls
toward belief and unbelief). This distinction determines the instrument: V2 (contaminated
conception of reason) is the wrong instrument for NS-12; V5 and fitrah-perspectives.md are
correct.

## About Noetic Structures

A noetic structure is the full set of propositions a subject believes together with the epistemic
relations among them: which beliefs are basic (not derived from others), which are non-basic
(inferred from others), the degree of firmness assigned to each, and which beliefs function as
load-bearing anchors for the rest.

Identifying the noetic structure is not optional — it determines which intervention has traction.
Addressing derived conclusions while leaving basic beliefs and implicit doxastic rules intact
achieves nothing; the structure will simply generate new protective rationalizations.

**Key diagnostic questions:**
- What does this person hold as *basic*?
- What *implicit doxastic rule* filters what they will count as evidence?
- Which belief is the *load-bearing anchor*?
- Where is the *intervention point* — the specific commitment most amenable to examination?

See `references/diagnostics/noetic-reading-checklist.md` for the shared definition and diagnostic
procedure.

<!-- END_SOURCE: profiles-index -->


## SOURCE MODULE: noetic-profiles

<!-- SOURCE: atomics/skill/references/case-library/noetic-profiles.md -->
<!-- MODULE_ID: noetic-profiles -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/noetic-profiles.md -->
<!-- SOURCE_SHA256: 3b5a0dae3c19f568312557993012d4009c3d7c725243c984d8bfc145a1ac2787 -->

---
id: noetic-profiles
module_class: case-library
canonical_path: skill/references/case-library/noetic-profiles.md
contract_version: "0.3.0.0"
load_when:
  - redirect only — do not load for profile content; use individual profiles/ files
routing_effects:
  - routes to per-profile files in profiles/
output_shapes:
  - pass-through
catalogue_registered: true
---

> REDIRECT — this file has been replaced by individual per-profile files under `profiles/`
> Do not load this file for profile content. Load the matched profile file from the table below.

# Noetic Structure Profiles — Redirect

NS profiles are now individually owned files in `case-library/profiles/`. Each profile is a
distinct canonical unit with its own frontmatter, IR field, and load discipline. Load only the
matched file — never load multiple profile files simultaneously.

## Routing Table

| NS code | Profile | File |
|---------|---------|------|
| NS-1  | Naturalist | `profiles/ns-1-naturalist.md` |
| NS-2  | Agnostic Evidentialist | `profiles/ns-2-agnostic-evidentialist.md` |
| NS-3  | Deconverted (Post-Religious) | `profiles/ns-3-deconverted.md` |
| NS-4  | Secular Moral Realist | `profiles/ns-4-secular-moral-realist.md` |
| NS-5  | Habituated Atheist | `profiles/ns-5-habituated-atheist.md` |
| NS-6  | Kalāmic Evidentialist | `profiles/ns-6-kalamic-evidentialist.md` |
| NS-7  | Theistic Evidentialist | `profiles/ns-7-theistic-evidentialist.md` |
| NS-8  | Muslim-Internal Crisis (Compound) | `profiles/ns-8-muslim-internal-crisis.md` |
| NS-9  | Historical-Critical Skeptic | `profiles/ns-9-historical-critical-skeptic.md` |
| NS-10 | Māturīdī Evidentialist | `profiles/ns-10-maturidi-evidentialist.md` |
| NS-11 | Fideist / Reformed Basic-Belief | `profiles/ns-11-fideist-reformed.md` |
| NS-12 | Blank-Slate or Dual-Nature Fiṭrah | `profiles/ns-12-blank-slate-dual-fitrah.md` |

For the full directory index, minimal-pair discriminators, and load discipline, see
`case-library/profiles/INDEX.md`.

<!-- END_SOURCE: noetic-profiles -->


## SOURCE MODULE: ns-1-naturalist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-1-naturalist.md -->
<!-- MODULE_ID: ns-1-naturalist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-1-naturalist.md -->
<!-- SOURCE_SHA256: c6299a75501f85207d00599634daaca52acbd4755a3883bb60f427c974f3326c -->

---
id: ns-1-naturalist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-1-naturalist.md
contract_version: "0.3.0.0"
load_when:
  - NS-1 (Naturalist) confirmed via Quick NS Identification
routing_effects:
  - V2 mandatory entry — empirical verifiability tribunal cleared before content
companions:
  - V2-reconstituting-reason
  - philosophical-usurpation
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# NS-1 — The Naturalist

**Implicit doxastic rule:** "A proposition is epistemically acceptable only if empirically testable
or logically derivable from empirically testable propositions."

**Load-bearing anchor:** Causal closure of the physical — the claim that the physical causal order
is complete and permits no intervention from non-physical causes.

**What the interlocutor holds as basic:** The reliability of sensory perception, the uniformity of
nature, the reality of the physical world, mathematical and logical truths. Crucially: the doxastic
rule itself is held as basic — not derived from anything, but functioning as the filter through
which all candidate beliefs must pass.

**Critical vulnerability:** The implicit doxastic rule is not itself empirically testable. "Only
empirically testable propositions are epistemically acceptable" cannot be established by empirical
testing — it is a meta-level philosophical commitment held as basic, yet it systematically excludes
theistic conclusions before they can be considered. This is iʿtiqādāt mawrūtha operating at the
level of basic beliefs, where it is invisible to the interlocutor. Additionally, the interlocutor
holds basic beliefs in other minds, the past, and mathematical objects — none empirically testable
in the required sense — revealing inconsistent application.

**Deformation type:** Primarily iʿtiqādāt mawrūtha; possibly ʿāda if the framework has been
habituated over many years.

**Intervention point:** Target the implicit doxastic rule, not the derived conclusions about God.
Deploy V2 (reconstitute the conception of reason): name the framework as historically contingent,
show it is not self-grounding, show it is not applied consistently. Only after the filter is
loosened can evidential content land.

<!-- END_SOURCE: ns-1-naturalist -->


## SOURCE MODULE: ns-2-agnostic-evidentialist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-2-agnostic-evidentialist.md -->
<!-- MODULE_ID: ns-2-agnostic-evidentialist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-2-agnostic-evidentialist.md -->
<!-- SOURCE_SHA256: 34919ed9a893b3749c73275d24a6943f5229c2be5d31b17f88b620c2ed6742fb -->

---
id: ns-2-agnostic-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-2-agnostic-evidentialist.md
contract_version: "0.3.0.0"
load_when:
  - NS-2 (Agnostic Evidentialist) confirmed via Quick NS Identification
routing_effects:
  - E2 inferential criterion before evidence content; V3 when regress demand active
companions:
  - E2-inferential-criterion
  - V3-regress-dissolution
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-2 — The Agnostic Evidentialist

**Implicit doxastic rule:** "Belief ought to be proportioned to evidence. Where evidence is
insufficient for a verdict, suspension of judgment is the epistemically virtuous response"
(Clifford's Principle / proportionality norm).

**Load-bearing anchor:** The proportionality norm itself — sincerely held as a mark of epistemic
integrity.

**What the interlocutor holds as basic:** Logical and mathematical truths, direct perceptual
deliverances, the reliability of memory and testimony within ordinary domains. The agnostic
genuinely holds some openness — God-belief is assigned very low credence, not zero.

**Critical vulnerability:** The proportionality norm, applied rigorously, would require suspension
of belief in other minds, the external world, the past, and the uniformity of nature — all of
which the agnostic holds without meeting the standard applied to theistic belief. The norm is
itself held as basic, without evidence proportioned to it. Once basic belief is acknowledged as
operating in the interlocutor's noetic structure, theistic basic belief is back on a par.

**Deformation type:** Primarily ẓann (operating on assumed-by-default positions taken as settled);
possibly genuine shubhah about specific arguments.

**Intervention point:** E2 (pressing the inferential criterion) combined with V3 (regress-
dissolution). The proportionality norm is a basic commitment not established by evidence
proportioned to it. Once this is visible, the interlocutor has already conceded the legitimacy of
basic belief — and theistic basic belief is in contention.

## Coverage Verification

- Failure condition: Do not emit NS-2 when the person already affirms God but demands inferential proof for warrant; that is NS-7, and V9 rather than E2 is the first move.
- IR-visible consequence: Emit `NS: NS-2`, match E2 and V3, and keep evidence-content held until the proportionality norm and regress pressure have been surfaced.
- Minimal pair: NS-2 differs from NS-6 because the NS-2 standard is agnostic suspension under evidential proportionality, while NS-6 is a kalamic obligation-of-inquiry frame inside an already theistic grammar.
- Hold/release rule: Hold affirmative case-building until the interlocutor concedes that basic belief already operates in their noetic structure; release E1/E3 only after that criterion clears.
- Anti-pattern guard: Do not answer the request for evidence by piling up evidences before the live evidence-standard has been made auditable.

<!-- END_SOURCE: ns-2-agnostic-evidentialist -->


## SOURCE MODULE: ns-3-deconverted

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-3-deconverted.md -->
<!-- MODULE_ID: ns-3-deconverted -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-3-deconverted.md -->
<!-- SOURCE_SHA256: 51e39a740d4084e69d1883db96f7bcd088b9fc252a22379950e51e1abaf7c5fe -->

---
id: ns-3-deconverted
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-3-deconverted.md
contract_version: "0.3.0.0"
load_when:
  - NS-3 (Deconverted / Post-Religious) confirmed via Quick NS Identification
routing_effects:
  - M4 grief-register gate before any DO content if grief-primary
companions:
  - M3-orphaned-intuition
  - P4-maieutic
  - M4-grief-register
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-3 — The Deconverted (Post-Religious)

**Implicit doxastic rule:** The deconversion narrative functions as the operative filter — new
information is evaluated through the lens of "what I now know I was deceived about."

**Load-bearing anchor:** The deconversion narrative itself — a self-story integrating past
religious experience (reinterpreted as self-deception or social pressure), present skepticism, and
a sense of intellectual progress. This anchor is *narrative*, not propositional.

**Critical vulnerability:** (a) The narrative does not explain the moral intuitions and
commitments the interlocutor still holds — orphaned from their former grounding. (b) Involuntary
theistic-type responses that persist (awe, gratitude without a recipient, moral horror without a
grounding) are unexplained by the deconversion narrative. (c) The "epistemic progress" framing
of the deconversion is itself typically taqlīd — absorption of a secular-intellectual community's
self-story without independent examination.

**Deformation types:** Hawā (the narrative has become identity-constituting); ẓann (the
deconversion is treated as the considered position when it is often absorbed); possibly gharaḍ if
social relationships are tied to the skeptical position.

**Intervention point:** Do not attack the narrative directly — this will harden resistance and is
experienced as an attack on the self. Instead, M3 (orphaned intuition probe): attend to what the
narrative does not explain. The Socratic-maieutic procedure (P4) is the appropriate extended
framework. Ask about what persists involuntarily — what arises in moments of beauty, loss, or
moral weight that the narrative cannot account for.

## Coverage Verification

- Failure condition: Do not use NS-3 merely because someone was formerly religious; the deconversion narrative must be the operative filter rather than a biographical fact.
- IR-visible consequence: Emit `NS: NS-3`; hold direct doctrinal rebuttal when grief, identity-performance, or narrative self-defense is primary; match M3/P4 and M4 where the affective register governs.
- Minimal pair: NS-3 differs from NS-5 because the load-bearing anchor is a departure story, not habituated atheism stabilized by the problem of evil and long-term intellectual habit.
- Hold/release rule: Hold attacks on the narrative itself; release M3 only through what the narrative fails to explain and release P4 when a seam of involuntary recognition is visible.
- Anti-pattern guard: Do not treat the deconversion story as an argument to refute directly; that hardens the identity frame the profile is meant to diagnose.

<!-- END_SOURCE: ns-3-deconverted -->


## SOURCE MODULE: ns-4-secular-moral-realist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-4-secular-moral-realist.md -->
<!-- MODULE_ID: ns-4-secular-moral-realist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-4-secular-moral-realist.md -->
<!-- SOURCE_SHA256: 316a583e7f70cdb3f7c40223c2879aa0335fea385072332d96c09a3aa9efe7eb -->

---
id: ns-4-secular-moral-realist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-4-secular-moral-realist.md
contract_version: "0.3.0.0"
load_when:
  - NS-4 (Secular Moral Realist) confirmed via Quick NS Identification
companions:
  - M3-orphaned-intuition
  - V5-directing-attention-signs
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-4 — The Secular Moral Realist

**Implicit doxastic rule:** "Moral facts are objective and mind-independent" — held with very
high firmness, often alongside rejection of theism.

**Load-bearing anchor:** Commitment to moral realism (torture is objectively wrong; human dignity
has inherent worth; these are not projections or social constructs).

**Critical vulnerability:** The interlocutor's deepest commitment — the objectivity of moral
facts — is in tension with their metaphysical framework. The available secular grounds for moral
realism (non-natural moral properties, Kantian rational legislation, quasi-realism) carry heavy
philosophical costs and remain deeply contested. The tradition's account — moral facts grounded
in the divine nature, the fiṭrah producing moral awareness as an āyah — is more parsimonious.
The interlocutor's commitment to moral realism is itself an instance of the fiṭrah's operation.

**Deformation types:** Primarily ẓann (the rejection of theism is assumed, not argued); possibly
iʿtiqādāt mawrūtha (secular moral realism absorbed from intellectual milieu).

**Intervention point:** Affirm the commitment to moral realism without qualification — it is
genuine and correct. Then deploy M3: given that moral facts are objective, mind-independent,
categorically binding, and reliably tracked by properly functioning human cognition — what kind of
universe makes this explicable? The secular options carry costs that become visible under
examination. This is not an argument against moral realism but an argument that moral realism's
most coherent grounding is theistic.

## Coverage Verification

- Failure condition: Do not emit NS-4 for ordinary ethical disagreement or moral relativism; the marker is firm objective moral realism held inside a secular metaphysical frame.
- IR-visible consequence: Emit `NS: NS-4`, match M3 and V5, and frame the live burden as grounding the moral fact the interlocutor already recognizes rather than attacking the moral judgment.
- Minimal pair: NS-4 differs from NS-8 moral recoil because NS-4 is external secular moral realism, while NS-8 is an internal believer crisis where pastoral disaggregation and P6/P7 may govern first.
- Hold/release rule: Hold critique of the moral intuition itself; release the grounding question only after affirming the moral recognition as genuine.
- Anti-pattern guard: Do not answer by weakening moral realism or treating the intuition as a projection; that destroys the profile's load-bearing anchor.

<!-- END_SOURCE: ns-4-secular-moral-realist -->


## SOURCE MODULE: ns-5-habituated-atheist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-5-habituated-atheist.md -->
<!-- MODULE_ID: ns-5-habituated-atheist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-5-habituated-atheist.md -->
<!-- SOURCE_SHA256: 306e154ea38580b56bf8915b20266a9522c91bcb597c9805d8424c4ab52e42c9 -->

---
id: ns-5-habituated-atheist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-5-habituated-atheist.md
contract_version: "0.3.0.0"
load_when:
  - NS-5 (Habituated Atheist) confirmed via Quick NS Identification
routing_effects:
  - F2 volitional dimensions mandatory first move before intellectual content
companions:
  - F2-volitional-dimensions
  - M4-grief-register
  - R2-the-reminder
  - V7-taqlid-check
  - M2-prior-probability
  - M1-self-refutation
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-5 — The Habituated Atheist

**Implicit doxastic rule:** God's non-existence has migrated from a conclusion to a basic belief
through extended intellectual habituation — held now without live reference to the arguments that
originally generated it.

**Load-bearing anchor:** The problem of evil — carrying both argumentative weight and the weight
of moral protest.

**Critical vulnerability:** (a) The evolutionary debunking argument, if successful, is
self-defeating (M1 — self-refutation). (b) The problem of evil as a probabilistic argument
depends on a prior probability assignment (M2 — prior probability probe). (c) The problem of
evil as presented is often a moral protest, not a philosophical argument (M4 — grief register).
(d) The will can become invested in the position, so argumentative engagement may deepen resistance
rather than clear it.

**Deformation types:** Primarily hawā (the will has dug in); possibly gharaḍ (social or
professional identity bound to the atheist position); ʿāda (the framework has been habituated
over years).

**Primary deformation:** Hawā — the compound-case sequencing rule requires acknowledging hawā
and gharaḍ before any intellectual content (seven-deformations.md §The Compound Case, rule 2).
ʿĀda is addressed alongside or immediately after the volitional barrier is acknowledged, not
before it, because hawā governs access to the case.

**Intervention point:** Relational engagement and F2 (foregrounding the volitional dimension)
before any argument. Do not supply new intellectual content while hawā governs the case — more
argument deepens resistance rather than clearing it.

**Opening-move hierarchy:**
1. If the presenting pressure is grief or moral protest, start with M4 (grief register).
2. If involuntary recognition remains near the surface, start with R2 (the reminder).
3. Otherwise use V7 (taqlīd check) to test whether the atheism being defended is actually
   examined rather than absorbed-by-default.
Use M2 or M1 only after the opening move has changed the next live differentiator.

## Coverage Verification

- Failure condition: Do not use NS-5 for a truth-seeking naturalist whose atheism is still an argued framework; that is normally NS-1, with V2/E1 rather than F2 as the opening move.
- IR-visible consequence: Emit `NS: NS-5`, mark F2 or M4/R2/V7 as the current matched opening, and keep M1/M2 held until the volitional or grief register no longer governs.
- Minimal pair: NS-5 differs from NS-3 because the stabilizer is habituated atheistic default and will-investment, not a deconversion narrative functioning as identity.
- Hold/release rule: Hold intellectual counters while hawa, gharad, or grief-primary posture governs; release M2/M1 only after the opening move creates a fresh differentiating signal.
- Anti-pattern guard: Do not reward habituated resistance with an argument dump; more content can deepen the very resistance the profile diagnoses.

<!-- END_SOURCE: ns-5-habituated-atheist -->


## SOURCE MODULE: ns-6-kalamic-evidentialist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-6-kalamic-evidentialist.md -->
<!-- MODULE_ID: ns-6-kalamic-evidentialist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-6-kalamic-evidentialist.md -->
<!-- SOURCE_SHA256: 2f778ac312a5a48f557831c5e8e27922cddfec392a05de405c2c5cc22cd6128a -->

---
id: ns-6-kalamic-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-6-kalamic-evidentialist.md
contract_version: "0.3.0.0"
load_when:
  - NS-6 (Kalāmic Evidentialist) confirmed via Quick NS Identification
routing_effects:
  - school identification required before V2; V2 mandatory after school confirmed
companions:
  - V2-reconstituting-reason
  - P3-reason-revelation-tension
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# NS-6 — The Kalāmic Evidentialist

**Implicit doxastic rule:** "Religious belief counts as knowledge only when it is grounded in
discursive dalīl; belief held without inferential demonstration is at best taqlīd and does not yet
have full epistemic standing."

**Load-bearing anchor:** The restriction of necessary knowledge to a narrow class together with the
claim that naẓar is the required route by which belief about God becomes knowledge.

**What the interlocutor holds as basic:** Logical axioms, direct sensory deliverances, and
mutawātir testimony are treated as foundational. The interlocutor also treats it as effectively
basic that anything outside this narrow necessary class must be inferentially demonstrated before
it may count as knowledge.

**Critical vulnerability:** The framework is narrower than the interlocutor's own practice. It does
not match how memory, other minds, ordinary testimony, and many settled convictions are actually
held. The requirement of naẓar also depends on the very fiṭrī reliability it demotes: inferential
reasoning cannot certify itself from nowhere. Finally, the prophetic pattern is sign-direction and
recognition before demonstration, so the framework mistakes a remedial path for the universal first
path of belief.

**Deformation types:** Primarily iʿtiqādāt mawrūtha; often ẓann where the evidentialist restriction
has been inherited as though it were self-evident reason itself.

**Primary deformation:** Iʿtiqādāt mawrūtha governing what the interlocutor will even allow to count
as knowledge before the case is heard.

**Intervention point:** Load `references/diagnostics/kalamic-interlocutor.md` and run the school
identification step before committing the IR's restoration target or matched modules. School
identification is not optional — the restoration target, load conditions, and prohibited moves
differ by school and by burden type.

*School identification consequences:*
- **If Māturīdī confirmed:** re-assign NS code to NS-10 before dispatch; do not continue as
  NS-6. Load NS-10 profile and the Māturīdī section of `kalamic-interlocutor.md`.
- **If Muʿtazilī or Ashʿarī confirmed (epistemological burden):** V2 is the primary instrument;
  target the foundationalist restriction's circularity; see `kalamic-interlocutor.md`
  §Downstream Routing Table for school-specific prohibited moves.
- **If Muʿtazilī or Ashʿarī confirmed (ontological burden — divine attributes or speech live):**
  the restoration target shifts to a school-specific ontological target (ḥudūth/khalq
  distinction for Muʿtazilī; kalām nafsī doctrine for Ashʿarī); §6.2 of
  `sound-reason-epistemology.md` and V8 must load; `do-attribute-precision.md` is the
  precision fixture source. Do not route the ontological burden through a generic bilā kayf
  treatment — the school-specific error must be named.
- **If school is unclear (provisional):** deploy the naẓar-circularity argument as a
  school-neutral opening; complete identification before committing the restoration target.

*Burden check:* When the interlocutor is pressing both epistemological framework and ontological
position simultaneously, sequence the IR to address epistemological burden first, ontological
second. The two burdens have different restoration targets; flattening them into one dispatch
is a routing failure.

P3 (reason-revelation tension) loads when the framing is explicitly reason versus revelation.
Ḥusn al-naẓar remains available as a secondary restorative path for impaired recognition, not
as the universal precondition of warranted belief.

<!-- END_SOURCE: ns-6-kalamic-evidentialist -->


## SOURCE MODULE: ns-7-theistic-evidentialist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-7-theistic-evidentialist.md -->
<!-- MODULE_ID: ns-7-theistic-evidentialist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-7-theistic-evidentialist.md -->
<!-- SOURCE_SHA256: 90f741583a2402bc2612d3b750f9e42fcf3609874198e507f52f64c56a04621e -->

---
id: ns-7-theistic-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-7-theistic-evidentialist.md
contract_version: "0.3.0.0"
load_when:
  - NS-7 (Theistic Evidentialist) confirmed via Quick NS Identification
routing_effects:
  - V9 necessary-knowledge priority mandatory first move
companions:
  - V9-necessary-knowledge-priority
  - V7-taqlid-check
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-7 — The Theistic Evidentialist

**Implicit doxastic rule:** "Belief in God is warranted only when established by inferential
argument from premises the interlocutor antecedently accepts. Recognitional warrant (fiṭrah),
testimonial warrant (khabar), and non-inferential basic-belief warrant do not yet count as
knowledge of God — they require inferential demonstration first."

**Load-bearing anchor:** Classical natural-theology or philosophical-theology apparatus (cosmological
argument, fine-tuning, ontological argument, Bayesian natural theology, perfect-being theology)
held as the *precondition* for warranted belief rather than as one legitimate path among others.
The anchor is the evidentialist restriction itself, not any one argument. The restriction is
typically inherited from the kalāmic evidentialist line (wujūb al-naẓar) — the same inheritance
that anchors NS-6 — but NS-7 is distinct in direction: the interlocutor already affirms God, and
so reads any pressure on the restriction as pressure on theism itself.

**What the interlocutor holds as basic:** Logical axioms, mathematical truth, direct perception,
the reliability of memory. The evidentialist restriction on religious warrant is held as basic
without being applied symmetrically to these other domains.

**Critical vulnerability:** (a) The standard is not applied symmetrically — other basic beliefs
are held without inferential demonstration. (b) The fiṭrī / recognitional warrant is demoted to
"mere feeling" by a rule that itself cannot be grounded the way it requires other beliefs to be
grounded. (c) The prophetic pattern is sign-direction and recognition preceding demonstration —
the evidentialist order reverses this. (d) A theology built on the evidentialist restriction is
brittle: when an argument falls, the belief it was meant to ground falls with it.

**Deformation types:** Primarily iʿtiqādāt mawrūtha (the evidentialist restriction is inherited
from a philosophical-theological tradition, not from the prophetic tradition); often ẓann (the
restriction is held as examined when it is actually absorbed). The theistic surface can conceal an
underlying naturalist epistemology.

**Intervention point:** Do *not* attack the inferential arguments themselves — the interlocutor
reads this as an attack on theism. Deploy V9 (necessary-knowledge priority): the fiṭrah's
deliverance of the Creator is ḍarūrī, not iktisābī; inferential argument is a legitimate
*restorative* or *remedial* route that can itself produce knowledge when the fiṭrah is occluded,
but it is not the universal precondition of warranted belief. Use V7 symmetrically on the
evidentialist restriction: have you examined the restriction itself, or inherited it?

**Opening-move hierarchy:**
1. V9 first: establish that non-inferential warrant is the norm, not the exception.
2. Then V7 symmetric: examine the evidentialist restriction itself.
3. Only after 1–2 do the apologetic arguments get re-positioned as scaffolding, not foundation.

## Coverage Verification

- Failure condition: Do not use NS-7 for a fideist or Reformed basic-belief holder who denies the need for inferential proof; that is NS-11 and routes first through R3.
- IR-visible consequence: Emit `NS: NS-7`, match V9 before apologetic argumentation, and record the evidentialist restriction as the live routing gate.
- Minimal pair: NS-7 and NS-11 are opposite theistic profiles: NS-7 over-requires inference, while NS-11 rightly affirms basic belief but may use a weaker proper-function frame.
- Hold/release rule: Hold critique of theism's arguments; release them only after V9 and V7 reposition inference as scaffolding rather than foundation.
- Anti-pattern guard: Do not attack cosmological or fine-tuning arguments first; the interlocutor may hear that as an attack on theism rather than on the evidentialist restriction.

<!-- END_SOURCE: ns-7-theistic-evidentialist -->


## SOURCE MODULE: ns-8-muslim-internal-crisis

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-8-muslim-internal-crisis.md -->
<!-- MODULE_ID: ns-8-muslim-internal-crisis -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-8-muslim-internal-crisis.md -->
<!-- SOURCE_SHA256: 58cd566eeb45bd59c358d6e0cea74e761e65b5934a69b4270906ef6536d78fcf -->

---
id: ns-8-muslim-internal-crisis
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-8-muslim-internal-crisis.md
contract_version: "0.3.0.0"
load_when:
  - NS-8 (Muslim-Internal Crisis) confirmed via Quick NS Identification
routing_effects:
  - disaggregation via P6 required before routing to doctrinal modules
  - P7 Stop-1 and Stop-3 commonly active
companions:
  - P6-universal-aqidah-principle
  - P7-restoration-stops
  - V10-transmission-content-vetting
  - revelation-transmission
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-8 — The Muslim-Internal Crisis (Modernist Revisionism / Authority-Fatigue Compound)

**Implicit doxastic rule:** The live rule is unstable and compound. Three commitments pressure one
another: (a) "Islam must be defensible by the standards of the modern discourse I am situated in"
(modernist evidentialism); (b) "The traditional authorities have failed morally or epistemically"
(authority-fatigue, often with specific incidents driving it); (c) "Reason and transmitted text are
in conflict on [X]" (taʿāruḍ anxiety, typically over a specific verse, ḥadīth, or classical ruling).

**Load-bearing anchor:** Not a single proposition but a *compound* — the interlocutor is holding
authority-fatigue plus moral-recoil plus textual-historical pressure simultaneously, and each is
reinforcing the others. Disaggregation is the first move.

**What the interlocutor holds as basic:** ʿAqīdah commitments still hold at the fiṭrī level — the
subject still prays, still recognizes the Qurʾān's authority at a level deeper than the surface
discourse. But the basic-belief structure has been destabilized: commitments that were firm now
feel provisional. Moral-intuition commitments (often modern liberal-secular) are held at near-ḍarūrī
firmness, and the perceived conflict between these intuitions and a classical ruling is what
precipitates the crisis.

**Critical vulnerability:** The compound nature is itself the vulnerability. Each element, in
isolation, would be tractable: authority-fatigue addresses by distinguishing institutional failure
from doctrinal truth; moral-recoil addresses by distinguishing modern liberal premises from the
tradition's moral-ontological premises; taʿāruḍ addresses by the reason-revelation tension procedure. The
interlocutor presents them compounded precisely because the compound is more stable than any
single element would be. Disaggregation releases them to be addressed.

**Deformation types:** Compound. The taʿāruḍ-surface is often shubhah covering hawā (moral recoil
at a ruling) or gharaḍ (social stake in modernist circles). Authority-fatigue can function as
iʿtiqādāt mawrūtha (absorbed framework). The compound must be diagnosed before the intervention
is chosen.

**Intervention point:** This case does *not* route directly to a case-library module. It routes
first to `references/procedures/` for the longer P-procedure that handles Muslim-internal crisis
(see P6 / mixed-case-handling.md), then to the matched sub-module per disaggregated component:
- Taʿāruḍ-surface → reason-revelation tension procedure; V2 on the modern hermeneutic that sets up the conflict
- Moral-recoil → M3 (orphaned intuition probe) on the modern moral commitments that produce the
  recoil; do not concede their foundation-status uncritically
- Authority-fatigue → Distinguish the institutional from the doctrinal; name the historical
  incidents honestly; do not defend the indefensible; do not let institutional failure become a
  warrant for doctrinal revision

**Register note:** This is a pastoral case before it is a doctrinal one. Intellectual engagement
without relational register frequently worsens the crisis. The pastoral-first ordering is a
practical inference: when ulterior motive, whim, or shubhah are active fiṭrah-suppressors,
cognitive intervention on a destabilized person tends to misfire before the stabilizing conditions
are in place.

---

## Compound Presentation Playbooks (NS-8)

These playbooks compile the compound-case sequencing rules from
`references/diagnostics/seven-deformations.md §The Compound Case` into NS-8-specific named
sequences. P7 stop references are explicit; see `references/procedures/P7-restoration-stops.md`
for mandatory and prohibited actions under each stop.

### Playbook (i) — Authority-Fatigue + Textual Pressure

**Intervention order:**
1. Address the authority-wound before engaging the textual argument.
2. Determine whether the textual claim would still be operative if the authority-wound were healed — in many NS-8 cases, it would not.
3. Deploy V10 and the matched RT case only after the authority-wound has been acknowledged.

**Reassessment trigger:** Interlocutor separates "I'm hurt by what happened in this institution" from "I have genuine doubts about this text-history question."

**Stopping condition:** If the interlocutor re-collapses the textual question into the authority grievance as soon as the intellectual engagement begins, the wound is still primary. Return to the relational register.

**P7 stops:** Stop 1 (Content-Withholding Stop) and Stop 3 (Relational-Repair-First Stop) both apply. Do not deploy V10 or textual counter-arguments into an unaddressed institutional wound.

---

### Playbook (ii) — Moral Recoil + Historical Criticism

**Intervention order:**
1. Identify whether the moral recoil — a ḥadīth found troubling, a ruling perceived as unjust — is the governing concern, with historical criticism recruited as corroboration after the fact.
2. If moral recoil is primary, address it directly; historical-critical arguments engaged alone will not resolve the underlying moral discomfort.
3. Only after the moral recoil is acknowledged, assess whether the historical-critical claim still needs independent engagement.

**Reassessment trigger:** Interlocutor explicitly engages the moral question independently of the historical-critical framing.

**Stopping condition:** If resolving the historical-critical point does not visibly reduce the moral distress, the moral recoil is primary. Argument alone is not the remedy.

**P7 stop:** Stop 1 applies — moral recoil is a form of protest that must be acknowledged before content is deployed.

---

### Playbook (iii) — Inherited-Trust Collapse + Evidential Demand

**Intervention order:**
1. Check whether the evidential demand ("show me evidence") has emerged from inherited trust having collapsed — the interlocutor previously accepted religious claims on communal trust and now rejects that as a basis.
2. If the demand for evidence is a response to trust-collapse rather than a principled evidentialist starting point, do not satisfy the demand within its own terms before addressing the trust history.
3. Apply V2 (framework-clearing) on the evidential criterion after identifying whether it is genuinely held or instrumentally deployed.

**Reassessment trigger:** Interlocutor distinguishes between "I no longer trust my community's testimony" and "I now hold a principled evidentialist criterion."

**Stopping condition:** If V2 produces no movement and the evidential demand remains fixed, check whether the demand is covering gharaḍ or hawā. If so, route to Stop 1.

**P7 stop:** Stop 4 (Underdetermined-Case Stop) applies if the read between genuine evidentialist and trust-collapse is not yet settled. Do not supply evidential content before the diagnosis is confirmed.

## Coverage Verification

- Failure condition: Do not route directly to a doctrinal module when the case is still a compound authority-fatigue, moral-recoil, and textual-pressure crisis; disaggregation is the owner-local first move.
- IR-visible consequence: Emit `NS: NS-8`, match P6 or mixed-case-handling first, surface any P7 Stop-1/Stop-3/Stop-4 condition, and mark downstream V10/RT/M3 content as held until the component read is stable.
- Minimal pair: NS-8 differs from NS-4 because moral pressure is internal to a destabilized believer's authority relation, not secular moral realism outside the tradition.
- Hold/release rule: Hold textual or moral counter-content until the playbook's reassessment trigger separates the wound, moral recoil, and transmission issue.
- Anti-pattern guard: Do not defend everything at once; simultaneous content release reinforces the compound rather than resolving it.

<!-- END_SOURCE: ns-8-muslim-internal-crisis -->


## SOURCE MODULE: ns-9-historical-critical-skeptic

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-9-historical-critical-skeptic.md -->
<!-- MODULE_ID: ns-9-historical-critical-skeptic -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-9-historical-critical-skeptic.md -->
<!-- SOURCE_SHA256: 7f8a403be30d27fb9ff271e1b16ae0f25012775f5d03c11e1df632638699f19c -->

---
id: ns-9-historical-critical-skeptic
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-9-historical-critical-skeptic.md
contract_version: "0.3.0.0"
load_when:
  - NS-9 (Historical-Critical Skeptic) confirmed via Quick NS Identification
routing_effects:
  - V2 mandatory first on imported historical-critical framework
  - V10 mandatory for separating artifact from authenticated transmission
companions:
  - V2-reconstituting-reason
  - V10-transmission-content-vetting
  - revelation-transmission
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-9 — The Historical-Critical Skeptic

**Implicit doxastic rule:** "Religious texts must be reconstructed by the methods of secular
historical criticism — manuscript genealogy, redaction analysis, form criticism, source criticism
— before any claim grounded in them can be credited. Until the reconstruction is complete, the
text cannot ground doctrine. Transmission through tradition is suspicious testimony; manuscript
collation is neutral method."

**Load-bearing anchor:** The methodological primacy of secular historical criticism, typically
imported from a framework developed for the New Testament (with its specific transmission
conditions) and applied to the Qurʾān as if the conditions were analogous. The interlocutor
frequently does not recognize the imported conditions as conditions.

**What the interlocutor holds as basic:** The reliability of manuscript-critical method itself;
the neutrality of the secular academic discipline; the assumption that variance in manuscripts
indicates textual instability in the doctrinal sense; the flattening of tawātur into single-strand
chain-of-custody reasoning.

**Critical vulnerability:** (a) Tawātur is not a chain of custody — it is a simultaneous
multi-path mass-transmission producing ḍarūrī knowledge, whose epistemic force is structurally
different from the single-strand textual transmission that historical criticism was built to
evaluate. (b) The *specific conditions* under which New-Testament historical criticism was
developed — no isnād system, a late and disputed canon, a fluid "live text" with documented
scribal harmonization, no living mutawātir recitational community — are what licensed the method
there. None of those conditions obtain for the Qurʾān. Importing the method without naming and
examining those conditions carries parasitic assumptions. (c) Qirāʾāt are not manuscript variants
in the Western text-critical sense — they are authorized recitational readings traced to the
Prophet via mutawātir ḥadīth, not scribal accidents. Reading them as evidence of textual
corruption is a category error (K-1). (d) The claim to methodological neutrality is itself
iʿtiqādāt mawrūtha: secular historical criticism carries specific philosophical commitments
(methodological naturalism, suspicion of testimony) that are not neutral.

**Deformation types:** Primarily iʿtiqādāt mawrūtha (an imported framework treated as neutral
method); often ẓann (the method is held as examined when the conditions of its application have
not been examined); sometimes shubhah (the specific manuscript-claim does have intellectual content
once the framework is loosened, but the intellectual content is narrower than the claim being made).

**Intervention point:** Routes to `case-library/revelation-transmission.md` via V10 (separating
artifact from authenticated transmission). The NS-9 profile alone is insufficient — the live issue
(RT-1, RT-2, or RT-3) determines the matched module. The order of operations:
1. V2 on the imported framework: name the specific conditions under which historical criticism was
   developed; show the conditions are not analogous.
2. V10 (separate artifact from authenticated transmission): the manuscript, fragment, or textual
   variant is an *artifact*; authenticated transmission is what carries the epistemic weight.
3. Only then engage the specific case — RT-1, RT-2, or RT-3 — by the matched module.

**Register note:** The interlocutor often presents as truth-seeking (`truth-seek` DO-orient) and
the scholarship is real. The diagnostic is not suspicion of the interlocutor but of the imported
framework. V2 is applied to the method, not to the person.

## Coverage Verification

- Failure condition: Do not emit NS-9 for any manuscript question by itself; the historical-critical method must be functioning as an imported neutral tribunal.
- IR-visible consequence: Emit `NS: NS-9`, match V2 before V10/RT, and keep the specific RT route held until the imported method's jurisdiction is named.
- Minimal pair: NS-9 differs from an RT-only case because NS-9 is about the governing method and its imported conditions, while RT-1 through RT-4 classify the transmission pressure after the method is cleared.
- Hold/release rule: Hold artifact-level rebuttal until V2 has named the method's source-conditions and V10 has separated artifact from authenticated transmission.
- Anti-pattern guard: Do not defend isolated fragments inside the historical-critical frame as though that frame were the neutral court.

<!-- END_SOURCE: ns-9-historical-critical-skeptic -->


## SOURCE MODULE: ns-10-maturidi-evidentialist

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-10-maturidi-evidentialist.md -->
<!-- MODULE_ID: ns-10-maturidi-evidentialist -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-10-maturidi-evidentialist.md -->
<!-- SOURCE_SHA256: 2f657b6500946a3b53335455348945c177eb4e1a0cc97c37a07ff3236e89eaec -->

---
id: ns-10-maturidi-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-10-maturidi-evidentialist.md
contract_version: "0.3.0.0"
load_when:
  - NS-10 (Māturīdī Evidentialist) confirmed via Quick NS Identification
routing_effects:
  - Māturīdī-specific school section required before V9; V9 primary technique
companions:
  - V9-necessary-knowledge-priority
  - P3-reason-revelation-tension
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# NS-10 — The Māturīdī Evidentialist

**Implicit doxastic rule:** "Innate fiṭrī recognition constitutes some basis for theistic inclination,
but full epistemic warrant — knowledge (ʿilm) rather than mere ẓann — requires naẓar (rational
investigation). The fiṭrah is not self-sufficient for warrant; it is a pull toward investigation
that must then be completed by discursive argument."

**Distinguishing from NS-6 (Kalāmic Evidentialist):** NS-6 is typically Ashʿarī in origin and
requires naẓar as an obligatory precondition before theistic belief is even licit (wujūb al-naẓar
in its hard form). NS-10 is Māturīdī: the fiṭrah is already acknowledged as genuinely inclined
toward God, and naẓar is presented not as a replacement for fiṭrī recognition but as its
confirmatory complement. This appears as a concession to the prophetic tradition — the fiṭrah is
affirmed — while still demoting its epistemic standing from ḍarūrī (necessary, self-sufficient)
to preparatory. The demotion is less obvious and more resistant to correction precisely because it
sounds like a middle position.

**Load-bearing anchor:** The claim that ḍarūrī knowledge requires naẓar for completion in the
domain of theistic belief — that fiṭrī recognition without discursive supplement is ẓann rather
than ʿilm.

**Critical vulnerability:** (a) The Māturīdī concession that the fiṭrah is inclined toward God
implicitly grants everything the tradition requires: if the fiṭrah reliably points toward the
Creator, then what it points to is not ẓann. (b) The restriction collapses the ḍarūrī/iktisābī
distinction at the site where the tradition most carefully maintains it: knowledge of God's
existence is ḍarūrī precisely because it is grounded in the fiṭrah, not in argument. (c) The
concessive position, if accepted, would require the prophets to have opened by demanding naẓar —
which they did not.

**Deformation types:** Iʿtiqādāt mawrūtha (the concessive restriction is absorbed from a school
tradition rather than derived from the prophetic sources); sometimes ẓann where the distinction
between ḍarūrī and ẓann-via-fiṭrah has been assumed rather than examined.

**Intervention point:** Load `references/diagnostics/kalamic-interlocutor.md` (Māturīdī section)
for the full treatment. The key epistemological move: affirm the fiṭrah's orientation toward God
(the interlocutor already concedes this), then press on whether the conceded orientation
constitutes epistemic standing or requires supplementary naẓar before standing is achieved. V9
(necessary-knowledge priority) is the primary technique: the fiṭrah's deliverance is ḍarūrī, not
iktisābī; confirming this is not adding to what was conceded but drawing out its implication.

*Burden check:* When the interlocutor's position also involves divine attributes or speech
(ontological burden live), the NS-10 ontological restoration target is the same as Ashʿarī
ontological (shared Kullābī inheritance); see `kalamic-interlocutor.md` §Downstream Routing
Table, NS-10 ontological row. §6.2 of `sound-reason-epistemology.md` and V8 must load for
that burden. Do not route the ontological dimension through the epistemological instrument
(V9 addresses the ḍarūrī/ẓann distinction; it does not address the ḥudūth/khalq or kalām
nafsī problem).

**Register note:** This is often an in-house theological interlocutor — a student of kalām or a
madrasa-trained person who is genuinely trying to hold both fiṭrah and naẓar. The engagement is
internal to the tradition, not apologetic. The goal is restoring the correct epistemic order, not
winning an inter-school debate.

<!-- END_SOURCE: ns-10-maturidi-evidentialist -->


## SOURCE MODULE: ns-11-fideist-reformed

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-11-fideist-reformed.md -->
<!-- MODULE_ID: ns-11-fideist-reformed -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-11-fideist-reformed.md -->
<!-- SOURCE_SHA256: 86c5409e2bd36297993768a0d4637fc6c2ebdb225a68fb1bd001e758d27be6ae -->

---
id: ns-11-fideist-reformed
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-11-fideist-reformed.md
contract_version: "0.3.0.0"
load_when:
  - NS-11 (Fideist / Reformed Basic-Belief Holder) confirmed via Quick NS Identification
routing_effects:
  - R3 warranted-basic-belief mandatory first move
companions:
  - R3-warranted-basic-belief
  - V5-directing-attention-signs
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-11 — The Fideist / Reformed Basic-Belief Holder

**Implicit doxastic rule:** "Belief in God is properly basic — it does not require inferential
justification because it is grounded in experience and the deliverances of the sensus divinitatis
(or a functionally analogous faculty). Any demand for inferential proof imposes the wrong epistemic
standard. The belief is warranted because it is formed through properly functioning faculties aimed
at truth."

**Distinguishing from NS-7 (Theistic Evidentialist):** NS-7 already believes but insists the
belief must be inferentially grounded. NS-11 already believes *and* insists it need not be. They
appear similar — both are theists — but require opposite interventions. NS-7 needs to be loosened
from the evidentialist restriction; NS-11 needs to be questioned about whether their basic-belief
warrant is actually ḍarūrī (grounded in the fiṭrah) or merely non-inferential (grounded in
Reformed epistemology's proper-function framework). The distinction matters because the two accounts
differ substantially in what is being held as basic and why.

**Load-bearing anchor:** The proper-function account of warrant (Plantinga) or a functionally
equivalent account. The belief is basic not because it is fiṭrī in the Islamic sense (a primordial
covenant-based orientation) but because it is formed by properly functioning faculties in an
appropriate environment. This is a weaker and more philosophically contingent anchor than the
fiṭrah.

**Critical vulnerability:** (a) If "properly functioning faculties" is doing the epistemic work,
then any report of properly functioning faculties that delivers God is sufficient — including fiṭrī
recognition. The tradition's account of the fiṭrah subsumes the proper-function account rather than
being subsumed by it. (b) The proper-function account gives no basis for distinguishing between the
deliverances of the prophetic tradition (waḥy) and the deliverances of any other claimed revelation
source; the tradition's fiṭrah-plus-tawātur account does make this distinction. (c) The fideist who
concedes that all properly functioning theistic belief is warranted has already granted the fiṭrah's
epistemic standing — the only question is whether the specific content being delivered is correctly
characterized.

**Deformation types:** Typically minimal — the interlocutor is truth-seeking and the basic-belief
stance is genuinely held. The deformation, if any, is iʿtiqādāt mawrūtha at the level of the
philosophical apparatus used to articulate the basic-belief stance (Reformed epistemology as the
only framework within which basic belief makes sense).

**Intervention point:** Do not attack the basic-belief thesis — it is broadly correct. Instead,
use R3 (warranted basic belief): place the fiṭrī account alongside the proper-function account as
a richer and more specific articulation of the same epistemic phenomenon. The goal is not to defeat
the Reformed account but to show that the tradition's account is more finely calibrated — it
specifies what faculty is operating (the fiṭrah), on what basis (the primordial covenant), with
what epistemic status (ḍarūrī), and what is required for its deliverances to be properly actualized
(āyāt, sound conditions). This is more, not less, than the proper-function account offers.

**Opening-move hierarchy:**
1. R3 (warranted basic belief): affirm the basic-belief structure; introduce the fiṭrah as the
   named faculty.
2. V5 (directing attention to signs): the āyāt are what actualize the fiṭrah's delivery; this is
   the Islamic specification of what "appropriate epistemic environment" means.
3. Only then, if the interlocutor presses on the distinction between Reformed and fiṭrī accounts,
   use the distinguishing argument above.

## Coverage Verification

- Failure condition: Do not use NS-11 for a theist who thinks belief must be inferentially proven before it is warranted; that is NS-7 and routes through V9.
- IR-visible consequence: Emit `NS: NS-11`, match R3 first, and treat V5 as the follow-up environment/signs move rather than an initial evidential demand.
- Minimal pair: NS-11 differs from NS-7 because NS-11 affirms basic belief while NS-7 treats inference as the universal precondition of warrant.
- Hold/release rule: Hold direct critique of basic belief; release the fitrah comparison only by affirming the basic-belief structure and then specifying it more precisely.
- Anti-pattern guard: Do not collapse Reformed basic belief into irrationalism; the profile's point is to refine a partly correct warrant structure.

<!-- END_SOURCE: ns-11-fideist-reformed -->


## SOURCE MODULE: ns-12-blank-slate-dual-fitrah

<!-- SOURCE: atomics/skill/references/case-library/profiles/ns-12-blank-slate-dual-fitrah.md -->
<!-- MODULE_ID: ns-12-blank-slate-dual-fitrah -->
<!-- MODULE_CLASS: case-library -->
<!-- CANONICAL_PATH: atomics/skill/references/case-library/profiles/ns-12-blank-slate-dual-fitrah.md -->
<!-- SOURCE_SHA256: 6da0b0741398b08c8c100bd9f90fa4214c93ef62ff4d857b99833a28f0c17599 -->

---
id: ns-12-blank-slate-dual-fitrah
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-12-blank-slate-dual-fitrah.md
contract_version: "0.3.0.0"
load_when:
  - NS-12 (Blank-Slate or Dual-Nature Fiṭrah Holder) confirmed via Quick NS Identification
companions:
  - V5-directing-attention-signs
  - E4-cross-cultural-check
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
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

# NS-12 — The Blank-Slate or Dual-Nature Fiṭrah Holder

**Implicit doxastic rule:** The fiṭrah either has no determinate religious content (blank-slate:
it is a general capacity that gets shaped by environment) or it contains equally weighted
orientations toward belief and unbelief (dual-nature: the fiṭrah pulls in two directions
simultaneously). In either case, the fiṭrah cannot ground theistic warrant specifically —
environmental or rational input is required to tip the balance.

**Distinguishing from NS-1 and NS-2:** NS-1 and NS-2 are externalist — they operate from a
secular framework that does not acknowledge the fiṭrah at all. NS-12 acknowledges the fiṭrah as
a genuine human faculty but disputes its content. This distinction matters: attacking scientism
(V2) is the wrong instrument against someone who already accepts the fiṭrah's reality but contests
its determinate deliverances.

**Load-bearing anchor:** The blank-slate claim: "The fiṭrah is a capacity for religiosity, not a
capacity for theism specifically — different environments actualize it differently." Or the
dual-nature claim: "The fiṭrah pulls toward both theism and atheism; the human being is equally
inclined in both directions, and the outcome depends on which pull is cultivated."

**Critical vulnerability:** (a) The blank-slate reading collapses the ḍarūrī/iktisābī
distinction: if the fiṭrah has no determinate content, knowledge of God's existence becomes
iktisābī (acquired by environmental input), which conflicts with the tradition's careful account
of why it is ḍarūrī. (b) The tawātur fiṭrī argument — the pan-human mass attestation of theistic
recognition — is evidence that the deliverances are not environmentally variable in the way
blank-slate posits; environmental variation at the surface does not refute the claim that the deep
orientation is determinate. (c) The dual-nature reading typically imports a psychology of moral
neutrality (the nafs ammāra / lawwāma / muṭmaʾinna series is being collapsed into a simple
equipoise) that the tradition explicitly distinguishes: the nafs is described as pulling toward
both higher and lower, but the fiṭrah as a distinct faculty is described as having a specific
orientation toward the Creator, not a neutral one. (d) Neither blank-slate nor dual-nature can
account for the specific phenomenology of involuntary theistic recognition — beauty, moral horror,
gratitude without recipient — that persists across environments and appears with an
object-directedness (toward a personal Creator) that blank-slate cannot explain.

**Deformation types:** Typically iʿtiqādāt mawrūtha (a specific reading of the fiṭrah absorbed
from a psychological or theological tradition, often without examining the tradition's own full
account). Sometimes ẓann — the dual-nature reading is often held without careful examination of
the distinction between the nafs's dual tendency and the fiṭrah's specific orientation.

**Intervention point:** Load `references/diagnostics/fitrah-perspectives.md` for the full
treatment of blank-slate and dual-nature positions. The primary technique is V5 (directing
attention to signs): the phenomenological argument — directing the interlocutor toward what their
own fiṭrī recognition actually delivers when functioning well — is more effective than the
propositional argument. The propositional argument (the tawātur fiṭrī thesis) is the secondary
move after the phenomenological engagement has opened the question. E4 (cross-cultural check) is
useful: if the fiṭrah's deliverances were environmentally determined in the way blank-slate posits,
one would not expect the specific cross-cultural convergence on a personal Creator over against
impersonal grounds of being.

**Register note:** This interlocutor is typically inside the tradition or sympathetic to it. The
dispute is exegetical and psychological, not theological at the root level. The goal is not to
overcome resistance to theism but to restore the tradition's own more precise account of the
fiṭrah's faculty and its determinate deliverances.

## Coverage Verification

- Failure condition: Do not use NS-12 for an external naturalist or agnostic who denies the fitrah altogether; NS-12 requires acceptance of the fitrah with dispute over its content.
- IR-visible consequence: Emit `NS: NS-12`, match fitrah-perspectives.md, and route to V5/E4 only after identifying whether the view is tabula-rasa or dual-nature.
- Minimal pair: NS-12 differs from NS-1/NS-2 because the interlocutor accepts a fitrah-like faculty and contests its determinate deliverance, rather than rejecting the faculty or suspending judgment.
- Hold/release rule: Hold broad anti-naturalist framework critique; release the positive-orientation account once the tabula-rasa or dual-nature confusion is identified.
- Anti-pattern guard: Do not treat the case as basic theism denial; it is a precision dispute inside or near the tradition's anthropology.

<!-- END_SOURCE: ns-12-blank-slate-dual-fitrah -->
