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
