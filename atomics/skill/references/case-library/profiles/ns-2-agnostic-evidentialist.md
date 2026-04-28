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
