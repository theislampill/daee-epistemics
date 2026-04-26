---
id: ns-12-blank-slate-dual-fitrah
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-12-blank-slate-dual-fitrah.md
contract_version: "0.2.2.0"
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
