---
id: ns-7-theistic-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-7-theistic-evidentialist.md
contract_version: "0.2.3.0"
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
