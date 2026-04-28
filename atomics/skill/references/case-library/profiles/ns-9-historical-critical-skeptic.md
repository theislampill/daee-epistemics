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
