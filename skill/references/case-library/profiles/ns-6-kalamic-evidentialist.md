---
id: ns-6-kalamic-evidentialist
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-6-kalamic-evidentialist.md
contract_version: "0.2.0.0"
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
---

> role: noetic structure profile — NS-6 Kalāmic Evidentialist
> use when: NS-6 confirmed via case-library/INDEX.md §Quick NS Identification; load this file only; do not confuse with NS-2 (see minimal-pair discriminator in profiles/INDEX.md) or NS-10 (Māturīdī variant)
> IR field: NS code = NS-6
> do not use when: NS code is still provisional — route through mixed-case-handling.md
> paired files: diagnostics/kalamic-interlocutor.md (mandatory — load to identify school position before V2); V2; P3 (reason-revelation tension)

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
