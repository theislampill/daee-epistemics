---
id: ns-11-fideist-reformed
module_class: case-library
canonical_path: skill/references/case-library/profiles/ns-11-fideist-reformed.md
contract_version: "0.2.3.0"
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
