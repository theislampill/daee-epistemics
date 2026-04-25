---
id: coverage-ledger
module_class: governance
canonical_path: skill/references/diagnostics/coverage-ledger.md
contract_version: "0.2.0.0"
load_when:
  - auditing whether a scope claim is backed by governed content
  - deciding which gap to close next
catalogue_registered: false
---

> role: parity/coverage audit ledger — explicit fidelity ratings for every recognized family and procedure in the skill; canonical source for distinguishing "already landed," "compressed but governed," "partial," and "missing/implied"
> use when: auditing whether a claim in SKILL.md, README, or a routing table is actually backed by governed content; updating after an edit pass; deciding which gap to close next
> do not use when: routing a live case — this file does not route; it describes what the routing apparatus covers and at what fidelity
> revision protocol: update the `last-audited` field and the affected row(s) after any edit pass; do not let the ledger go stale by making edits without updating it
> current-pass note: 2026-04 Session 10 (v0.1.4.0) — governance infrastructure and representation parity pass. No case-coverage ratings changed. Changes: pipeline canonical ownership declared for Recursive State-Transition View and Meta-Noetic Memetics sections; IR-to-case-state derivation map added to case-state-schema.md; hold / withheld / continuation-eligibility rules cross-referenced across routing-precedence.md, diagnostic-ir.md, and framework-pipeline.md; meta-noetic-memetics operationalization bounded to specific IR fields; compact pipeline equation ordering corrected; χ state-carry partition consolidated; alignment × recognition → continuation-eligibility table added; three-way activation partition named; positive termination condition distinguished; gate-trigger tracing added to IR schema; module-codes.md added to always-load set. | 2026-04 Session 11 (v0.1.4.1) — ghost-load prohibition pass. Rule 14 added to SKILL.md; ghost-load prohibition bullet added to diagnostic-ir.md §Current-pass activation rule; Ghost-Load anti-pattern added to anti-patterns.md with Quick Self-Audit item. No case-coverage ratings changed. | 2026-04 Session 12 (v0.2.0.0) — PF atomization and routing-surface architecture pass. DO family (do-core.md, do-second-loop.md, do-christian-extensions.md) converted to routing-surface files with load floors, fan-out tables, and 9-subsection structural headers. do-attribute-precision.md: Three-Layer Owner Distinction + Current-Pass/Held Distinction + Failure Tests added. philosophical-usurpation.md: Peer-File Routing Integration section added. case-library/INDEX.md: DO-Family Routing Architecture section added. pattern-profiling.md: PF-6 generalized to divine-plurality/worship-status structural pattern (cross-tradition; Christian Trinity is one overlay; do-christian-extensions.md is tradition-specific overlay only); PF-7 renamed to Prophetic credential / authority-ordering challenge; PF-6 scope note added; Owner Exception generalized to cover structural metaphysical burden patterns. terminology.md: ilāh/Allāh/false-ilāh worship-status entry expanded with fuller worship definition and PF-6 routing significance. anti-patterns.md: Transcendence Default / Abstraction-as-Cure entry added with Quick Self-Audit item. | 2026-04 Session 13 (v0.2.0.0) — Output-release rubric and diagnostic render contract pass. Created skill/references/rubrics/output-release.md (full runtime governance rubric with 9 pass/fail checks and 16 failure tests) and skill/references/rubrics/diagnostic-render-contract.md (3-level render contract: ordinary / compact diagnostic / full audit). SKILL.md: Rule 15 in JSON/IR Adherence (held = traversal-delayed; same-response recursion bounded by P7); Rule 8 in Named Routing Constraints (no held-as-never-answer); Output-Release Governance table added to Reference Architecture. framework-pipeline.md: ASCII chart extended with output-release rubric and render contract gates; 4 new forbidden shortcut paths; compact pipeline expression added. routing-precedence.md: §VII added (routing precedence vs. release vs. render; cumulative-build rule; anti-smuggling rule). P7-restoration-stops.md: preamble rider (held = traversal-delayed; diagnostic transparency does not suspend stop discipline); Stop-2 reassessment rule added. anti-patterns.md: 6 new anti-patterns added (Held-but-Answered Contradiction, Held-as-Never-Answer, State-Refresh-as-User-Reply-Only, Recursive Dump, Fixed Full-Field Template Materialization, Template-Driven Routing) — total now 22 named anti-patterns. No case-coverage ratings changed. | 2026-04 Session 14 (v0.2.0.0) — Machine-readable operative contracts pass. Created skill/references/diagnostics/operative-contracts.md (architecture spec: function, position, catalogue relation, required/optional YAML keys, examples by class, failure modes, migration strategy, linting plan) and skill/references/diagnostics/operative-contract.schema.json (JSON schema Draft 2020-12 for YAML operative front matter; required: id, module_class, canonical_path, contract_version; optional: load_when, routing_effects, emits, blocks, companions, output_shapes, p7_stops_governed, layer_constraint, catalogue_registered; module_class enum includes governance class for non-catalogue files). YAML operative front matter applied to 4 pilot files: M9-predication-mode.md (tactic), P7-restoration-stops.md (procedure), routing-precedence.md (governance, catalogue_registered: false), do-attribute-precision.md (case-library). SKILL.md: Per-File Operative Contracts table added after Dispatch Gate section. README.md: version reconciliation — v0.2.1.0 entries folded back into v0.2.0.0. No case-coverage ratings changed.
> last-audited: 2024-12 (Session 1 — kalāmic variance pass) + 2025-01 (Session 2 — parity ledger creation) + 2026-04 (Session 3 — pattern-family robustness audit + profile-patterning patch set) + 2026-04 (Session 5 — semantic-gate and owner-hardening pass for Volumes 1–4) + 2026-04 (Session 6 — integrative grokking pass) + 2026-04 (Session 8 — known-good governance restoration pass) + 2026-04 (Session 9 — selective worldview-deflection restoration pass) + 2026-04 (Session 10 — v0.1.4.0 governance infrastructure and representation parity pass) + 2026-04 (Session 11 — v0.1.4.1 ghost-load prohibition) + 2026-04 (Session 12 — v0.2.0.0 PF atomization and routing-surface architecture) + 2026-04 (Session 13 — v0.2.0.0 output-release rubric and render contract) + 2026-04 (Session 14 — v0.2.0.0 operative contracts pilot) + 2026-04 (Session 15 — artifact consolidation and gap-filling pass) + 2026-04 (Session 16 — operative front matter rollout + V-series direct-read verification) + 2026-04 (Session 17 — tactic direct-read verification + enhanced YAML front matter rollout) + 2026-04 (Session 18 — tactic patch pass: E2, M2, M3, M6, R1, R2, R3, F1 — all remaining L(~) tactic files upgraded to L(✓))

# Coverage Ledger — Parity Audit

## Legend

| Code | Meaning | Governance standard met |
|------|---------|------------------------|
| **L** | **Landed** | Canonical owner file; typed routing active (Quick NS/DO/RT table or dedicated frontmatter); IR-visible consequences (consistency rules, backbone predicate emissions, or restoration target binding); failure conditions or failure tests present; minimal-pair discriminator where a near-miss exists |
| **C** | **Compressed-but-governed** | No dedicated file of its own; fully routed through existing instruments with traceable dispatch consequences; activation is correct, but the content lives inside a larger file rather than a canonical owner |
| **P** | **Partial** | Has a file or section, but missing one or more key governance elements — no failure conditions, no IR rule, scope in SKILL.md or README overstates governed depth, or activation trigger is present but thin-basis discipline is absent |
| **M** | **Missing/implied** | Referenced in SKILL.md description, INDEX, or a routing table — but no dedicated content and no governed dispatch path; the claim is an ambient scope assertion, not a covered case |

**Audit confidence flags:**
- **(✓)** — directly read and confirmed in this or the prior session
- **(~)** — confirmed by cross-reference from files that depend on it; canonical file not directly read in this pass

---

## §1 — Noetic Structure Profiles (NS-1 through NS-12)

| NS code | Name | Rating | Canonical file | Key gap (if any) |
|---------|------|--------|---------------|-----------------|
| NS-1 | Naturalist | **L (✓)** | `profiles/ns-1-naturalist.md` | — |
| NS-2 | Agnostic Evidentialist | **L (~)** | `profiles/ns-2-agnostic-evidentialist.md` | — |
| NS-3 | Deconverted (Post-Religious) | **L (~)** | `profiles/ns-3-deconverted.md` | — |
| NS-4 | Secular Moral Realist | **L (~)** | `profiles/ns-4-secular-moral-realist.md` | — |
| NS-5 | Habituated Atheist | **L (~)** | `profiles/ns-5-habituated-atheist.md` | — |
| NS-6 | Kalāmic Evidentialist | **L (✓)** | `profiles/ns-6-kalamic-evidentialist.md` | School identification now mandatory before IR restoration target; Muʿtazilī/Ashʿarī sub-variants added Session 1 |
| NS-7 | Theistic Evidentialist | **L (~)** | `profiles/ns-7-theistic-evidentialist.md` | — |
| NS-8 | Muslim-Internal Crisis (Compound) | **L (~)** | `profiles/ns-8-muslim-internal-crisis.md` | Compound case playbooks in `mixed-case-handling.md`; moral-recoil sub-component under Type D philosophical usurpation is C (no dedicated DO treatment for Islamic-specific moral objections) |
| NS-9 | Historical-Critical Skeptic | **L (~)** | `profiles/ns-9-historical-critical-skeptic.md` | — |
| NS-10 | Māturīdī Evidentialist | **L (✓)** | `profiles/ns-10-maturidi-evidentialist.md` | Burden check for ontological dimension added Session 1 |
| NS-11 | Fideist / Reformed Basic-Belief | **L (~)** | `profiles/ns-11-fideist-reformed.md` | — |
| NS-12 | Blank-Slate or Dual-Nature Fiṭrah | **L (~)** | `profiles/ns-12-blank-slate-dual-fitrah.md` | — |

**Routing infrastructure:** `profiles/INDEX.md` — minimal-pair discriminators for NS-2/NS-6, NS-6/NS-10 (with Muʿtazilī/Ashʿarī sub-variant note), NS-7/NS-11, NS-1/NS-2/NS-12. Quick NS Identification table in `case-library/INDEX.md`. Both **L (✓)**.

**Legacy redirect:** `case-library/noetic-profiles.md` — redirect-only stub pointing to profiles/. Status: correctly deprecated, no content served from it.

---

## §2 — Doctrinal Objections Family (DO-1 through DO-15)

### DO-1 through DO-6 (do-core.md)

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-1 | Divine Hiddenness | **L (✓)** | Objection stated strongly, strongest rebuttal, operative response, remaining probe; P4 (maieutic) routing when search-narrative is live |
| DO-2 | Evidential Evil | **L (✓)** | Skeptical-theism rebuttal addressed; M4 routing when grief-primary; distinction between logical and evidential problem present |
| DO-3 | Evolutionary Debunking | **L (✓)** | M1 self-refutation check; targeted-defeater form; foundation/superstructure distinction; failure test added Session 15 |
| DO-4 | Religious Diversity | **L (✓)** | Discourse-orientation gate; V10/DO-14 for canon questions; genesis/justification distinction; failure test added Session 15 |
| DO-5 | Transcendence and Language | **L (✓)** | M9 semantic blocker required; V8 bilā kayf as honest acknowledgment; DO-13 discriminator; failure test added Session 15 |
| DO-6 | Attribute Coherence | **L (✓)** | M9 split required; DO-13 discriminator; Anselmian framing not tradition's primary ground; failure test added Session 15 |

**Failure-condition audit note:** do-core.md failure-test blocks added in Session 15 (Gap 3 closed). DO-3: M1 self-refutation check and foundation/superstructure distinction required; DO-4: discourse-orientation gate and V10/DO-14 routing for canon questions; DO-5: M9 semantic blocker and DO-13 discriminator; DO-6: M9 split required and DO-13 discriminator. All six DO-1 through DO-6 entries now rated L (✓).

### DO-7 through DO-10 (do-second-loop.md)

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-7 | Cognitive Science of Religion / HADD | **L (✓)** | M1 self-refutation check; targeted-defeater form; foundation/superstructure distinction; DO-7/DO-10 discriminator; failure test added Session 15 |
| DO-8 | Prophetic Mission and Moral Luck | **L (✓)** | M4 discriminator required; uneven-access strongest rebuttal; maintained-corruption distinction; failure test added Session 15 |
| DO-9 | Great Pumpkin | **L (✓)** | Tawātur-fiṭrī universality criterion as explicit discriminator; R3 scoping; failure test added Session 15 |
| DO-10 | Three-Tiered Epistemological Structure | **L (✓)** | "Proof" / "reason" disambiguation required before tier content; kalāmic school handling; tier-sequencing discipline; failure test added Session 15 |

**Failure-condition audit note:** do-second-loop.md DO-7 through DO-10 failure-test blocks added in Session 15 (Gap 3 closed). DO-7: self-refutation check and targeted-defeater form required; DO-8: M4 discriminator and uneven-access strongest rebuttal; DO-9: tawātur-fiṭrī universality criterion; DO-10: "proof" / "reason" disambiguation before tier content. All four entries now rated L (✓).

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-15 | Islamic-Specific Moral Objections (Imported-Criterion Form) | **L (✓)** | Added Session 15 (Gap 4 closed). Full entry in do-second-loop.md. NS-8 primary / NS-4 secondary pairing. FPD + Type D usurpation + V2 must precede content. Level A / Level B moral-claim distinction; four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma) as internal operative standard; conditions-application distinction for ḥudūd and historical slavery analysis; collapse-move failure tests (apology, historical-only dismissal, criterion concession). M4-grief-register gate for NS-8 affective register. |

### DO-11 through DO-14 (do-christian-extensions.md)

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-11 | Trinity from Divine Perfection | **L (✓)** | Hidden premise exposed; parody-pressure test; remaining probe; routing to V10 + RT-2 when argument must move to revelation |
| DO-12 | Logical Problem of the Trinity | **L (✓)** | Model-identification obligation; taxonomy of model families and how each fails; appeal-to-mystery not treated as resolution |
| DO-13 | Philosopher's God vs. God of Revelation | **L (✓)** | Aristotelian-stasis critique; bilā kayf route; minimal-pair discriminator vs. DO-5; "Remaining probe" serves as self-audit |
| DO-14 | Christian Canon Selection Confusion | **L (✓)** | Added Session 3 audit pass. Case-profile block; three sub-question discrimination (selection/formation/authorization); prohibited moves (diversity-as-conclusive; RT-2 collapse; premature Islamic answer); positive routing to DO-10 Tier 2 via criterion-gap opening; NS/deformation pairing (NS-7, NS-12, NS-3, NS-11); discourse-orientation gate (iʿrāḍ → register-hold) |

### Attribute Discourse Precision (do-attribute-precision.md)

| Confusion | Name | Rating | Notes |
|-----------|------|--------|-------|
| Confusion 1 | Category Mistake in Predication | **L (✓)** | Bad-output / corrected-output fixture; self-audit question; prohibited move; NS-6 ontological trigger added Session 1 |
| Confusion 2 | Illicit Analogy | **L (✓)** | Fixture with valid-range analysis |
| Confusion 3 | Equivocal Predication Without Marking | **L (✓)** | Univocal/analogical/equivocal distinction enforced |
| Confusion 4 | Composition Panic | **L (✓)** | Muʿtazilī/philosophical history; prohibited-move; §6.3 reference for tarkīb-iftiqār |
| Confusion 5 | Attribute-Multiplicity / Person-Multiplicity Conflation | **L (✓)** | Identity argument vs. composition argument correctly separated; Trinity routing confirmed |
| Confusion 6 | Perfect-Being Theology as Upstream Tribunal | **L (✓)** | Framework named as one position; allegorization prohibited |

---

## §3 — Revelation / Transmission Family (RT-1 through RT-4)

| RT code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| RT-1 | Manuscript/Fragment vs. Authenticated Transmission | **L (✓)** | Three sub-routes (provenance/contents/authority); cross-tradition contamination guard; worked examples (correct + incorrect) |
| RT-2 | Canon Formation vs. Inspired Authority | **L (✓)** | Recognition vs. creation distinction; contamination guard; minimal-pair discriminator vs. RT-1 |
| RT-3 | Qirāʾāt, Aḥruf, Manuscript Confusion | **L (✓)** | Three sub-routes; qirāʾāt ≠ scribal variants; contamination guard; worked examples |
| RT-4 | Muslim-Internal Textual-Historical Destabilization | **L (✓)** | Pastoral register governs before doctrinal; V10 classification first; P5 pairing; worked examples |

**V10 routing:** Mandatory before any RT entry; `V10-transmission-content-vetting.md` governs provenance → contents → authority sequence. Status: **L (~)** (referenced as mandatory in revelation-transmission.md frontmatter and from RT-2/RT-3 headings; file exists but not directly read in this pass). Session 4 generalize-upward pass added: (1) explicit `> scope:` cross-tradition statement in frontmatter; (2) named "Recognition vs. creation principle (cross-traditional)" in Step 3; (3) "Canon-authority structural form (cross-traditional)" block in Step 3 naming the criterion-circularity problem across Protestant/Catholic/Jewish/Hindu traditions with the shared logical form; (4) Branch B "Route after" updated to include DO-14 for Christian canon-selection/authorization cases; (5) DO-14 sub-question (c) now carries a structural pointer back to V10 Step 3 as the generalized owner. V10 is now the cross-traditional structural owner; DO-14 is its Christian instantiation.

**Surface-marker triage table:** Present in revelation-transmission.md with disambiguation logic and ambiguous-surface-case rules. **L (✓)**.

**Scope boundary:** RT family still covers Qurʾānic/scriptural transmission specifically. Ḥadīth corpus/authentication epistemology is now governed separately by `hadith-authentication-epistemology.md`, while Old/New Testament transmission in comparative Islamic perspective and the non-Qurʾānic sunnah preservation question as a full specialist case family remain outside the RT owner itself.

---

## §4 — Philosophical Usurpation Types (A through D)

| Type | Character | Rating | Notes |
|------|-----------|--------|-------|
| Type A | Aristotelian/Neo-Platonic Theism as Default Standard | **L (✓)** | Telltale features U-1/U-3/U-5; connected to DO-13 + prophecy-wahy-supremacy.md + Confusion 6 |
| Type B | Scientific Naturalism as Epistemic Gate | **L (✓)** | Telltale features U-1/U-2/U-4; connected to NS-1 + V2 + foreign-premise-detection |
| Type C | Historical-Critical Methodology as Hermeneutic Authority | **L (✓)** | Telltale features U-2/U-3/U-5; connected to NS-9 + V10 + revelation-transmission.md |
| Type D | Liberal Political Philosophy as Moral Arbiter | **L (✓)** | Telltale features U-1/U-3; connected to NS-8 + seven-deformations.md |

**Route consequences:** 5-step sequence (name usurpation → refuse tribunal → V2 on framework → restore authority order → engage content). **L (✓)**.

**Prohibited moves:** PM-1 through PM-4. **L (✓)**.

**Case-state emission format:** Route consequences and prohibited moves are explicit in the owner file; typed upstream/case-state fields remain carried by `foreign-premise-detection.md` plus case-state / IR. **L (✓)**.

**Gap (Type D) — resolved Session 15:** DO-15 (Islamic-Specific Moral Objections) now provides the full operative-response structure. Type D usurpation identification is L; the substantive response with Level A / Level B moral-claim distinction, four-foundations criterion, and conditions-application analysis is now L (✓). NS-8 primary / NS-4 secondary pairing in DO-15.

---

## §5 — Deformation Types (Seven Deformations)

| Deformation | Rating | Notes |
|-------------|--------|-------|
| Iʿtiqādāt mawrūtha (inherited beliefs) | **L (✓)** | Primary cue, first move, common confusion; V2 primary |
| Mushābara fāsida (1-A) — sub-type | **L (✓)** | Named sub-variant of iʿtiqādāt mawrūtha; distinguishing marker: one premise regenerates downstream conclusions even after local clearing; M1 applied to the premise itself |
| Hawā (volitional desire) | **L (✓)** | F2 or relational engagement; objections multiplying after clearing is the diagnostic signal |
| Ẓann (conjecture, unexamined assumption) | **L (✓)** | V7 (symmetric critique of taqlīd); distinguished from genuine shubhah |
| Taqlīd (imitation) | **L (✓)** | Taḥqīq invitation; distinguished from ẓann |
| ʿĀda (habituation) | **L (✓)** | V2 then V5; distinguished from iʿtiqādāt mawrūtha by phenomenology (distortion feels like direct reality) |
| Gharaḍ (interest/cost of inquiry) | **L (✓)** | F2; distinguished from hawā by the honesty of the inquiry being what is costly |
| Shubhah (genuine intellectual obstacle) | **L (✓)** | The one deformation that responds to intellectual engagement; V9 or matched case response; over-attribution to this deformation is the primary diagnostic error |

**Note on count:** The routing table has 8 rows for 7 deformations — mushābara fāsida (1-A) is a sub-type of iʿtiqādāt mawrūtha, not an eighth deformation. Both the count (7) and the sub-type (1-A) are correctly present in seven-deformations.md.

**Routing summary table:** Present in seven-deformations.md with primary cue, first move, prohibited first move, common confusion. **L (✓)**.

---

## §6 — Modes of Concealment

| Mode | Rating | Notes |
|------|--------|-------|
| Iʿrāḍ (turning away) | **L (✓)** | modes-of-concealment.md |
| Juḥūd (denial despite recognition) | **L (✓)** | modes-of-concealment.md |
| Inkār (rejection) | **L (✓)** | modes-of-concealment.md |
| Istikbār (arrogance) | **L (✓)** | modes-of-concealment.md |
| Nifāq (hypocrisy/insincerity) | **L (✓)** | modes-of-concealment.md |
| mode-? (indeterminate) | **L (✓)** | IR valid value when mode cannot be confirmed |
| compound | **L (✓)** | IR valid value for mixed concealment |

**modes-of-concealment.md** directly read and hardened in Session 9. Worldview-deflection /
pseudo-neutrality is now explicitly represented as a live route into concealment analysis and
bounded deployment rather than being left as a generic abstract label.

**Concealment × Orientation matrix:** Present in case-state-schema.md as an explicit 5-column × 6-row decision table (✓ direct read confirmed). Each cell specifies register rule, deployable action, and hold condition. Current status: **L (✓)**. The matching anti-pattern now exists in anti-patterns.md (`Register-Hold Bypass`), so the matrix and its failure signature are aligned.

---

## §7 — Governance Procedures

### Diagnostic Procedures (P1 through P7)

| Procedure | Rating | Notes |
|-----------|--------|-------|
| P1 — Fiṭrah Restoration | **L (~)** | Dedicated file; fiṭrah restoration sequence |
| P2 — Objection Mapping | **L (~)** | Dedicated file |
| P3 — Reason-Revelation Tension | **L (~)** | Dedicated file; paired with NS-6/NS-10 and V2 |
| P4 — Maieutic | **L (~)** | Dedicated file; DO-1 remaining probe routes here |
| P5 — Already-Believing | **L (~)** | Dedicated file; RT-4 routes here for pastoral sequencing |
| P6 — Universal ʿAqīdah Principle | **L (✓)** | Dedicated file; Session 9 restores an explicit worldview-deflection / pseudo-neutrality owner-local section and selective bounded-externalization branch |
| P7 — Restoration Stops | **L (✓)** | Five named stops with triggers, mandatory actions, prohibited actions, exit criteria, re-entry conditions |

**Session 9 regression note:** 0.1.1.0 weakened explicit worldview-deflection handling by
removing P6's dedicated owner-local section and the exact "I have no religion, I just follow
the evidence wherever it leads" fixture. The current pass restores that path in P6,
pattern-family-audit.md, modes-of-concealment.md, noetic-reading-checklist.md,
framework-pipeline.md, and SKILL.md as a first-class selective DSL-IR maneuver for
meta-epistemic / meta-noetic routing integrity, not a wording polish pass.

**Session 10 distillation note:** Third-wave repair adds a typed acceptance-state layer and
repo-wide governed-recursion doctrine rather than leaving them as a mainly local consequence
of M8 or P7. `diagnostic-ir.md`, `diagnostic-ir.schema.json`, `case-state-schema.md`,
`routing-precedence.md`, `SKILL.md`, and `P7-restoration-stops.md` now distinguish
`tribunal-loosened`, `frame-cleared`, `recognition-surfaced`, and `alignment-advanced`,
type `recognition_strength` and `continuation_eligibility`, and permit continuation only on
refreshed state. This is architectural distillation toward restorative selective routing, not
debate-momentum hardening.

### P7 Stops (individually)

| Stop | Rating | Notes |
|------|--------|-------|
| Stop 1 — Content-Withholding | **L (✓)** | Trigger: grief-primary or hawā confirmed; exit criteria require actual register shift |
| Stop 2 — One-Live-Question | **L (✓)** | Behavioral exit criterion (stopping is the criterion, not judging absorption) |
| Stop 3 — Relational-Repair-First | **L (✓)** | Trust addressed before argument; exit criteria require interlocutor-initiated inquiry |
| Stop 4 — Underdetermined-Case | **L (✓)** | Forced-read prohibition; provisional read discipline; Stop-4 as IR output when mandatory fields cannot be grounded |
| Stop 5 — Non-Contractual-Inquiry | **L (✓)** | Contractual status determined by interlocutor, not practitioner |

### Core Routing Infrastructure

| File | Rating | Notes |
|------|--------|-------|
| diagnostic-ir.md | **L (✓)** | Full IR schema; gate checks 1–6; mandatory minimum; consistency rules (including NS-6 school-specific rules added Session 1); compressed form; failure tests |
| routing-precedence.md | **L (~)** | Seven suppression rules; precedence hierarchy; not directly read but extensively cross-referenced |
| framework-pipeline.md | **L (~)** | Structural branching chart; paired with routing-precedence and diagnostic-ir |
| case-state-schema.md | **L (✓)** | Contains the concealment × orientation matrix as an explicit 5-column × 6-row decision table (confirmed direct read); each cell specifies the register rule and what is held vs. deployable; [Case State], [Source Basis], and [Restoration Trace] block schemas; `claim_level` is surfaced when higher-order burdens are live so they are not collapsed into first-order content |
| pattern-profiling.md | **L (✓)** | Canonical owner for `claim_level` and `pattern_profile`; keeps PF-1 through PF-12 as a routing overlay, makes claim-level conditional in routine first-order cases, and routes imported perfection/non-eventfulness through existing diagnostic owners rather than adding a PF code |
| noetic-reading-checklist.md | **L (✓)** | Shared NS definition; four key diagnostic questions (basic beliefs, implicit doxastic rule, load-bearing anchor, intervention point); Session 6 adds thin-basis / excerpt discipline plus pattern-profile hand-off; Session 9 adds explicit pseudo-neutral slogan checklist rider; Session 15 adds structured minimum-basis rule (Dimensions 1/4/8 convergence required, mandatory decisive-missing-differentiator, failure test) |
| anti-patterns.md | **L (✓)** | 11 named anti-patterns: the original seven plus Excerpt Over-Read, Register-Hold Bypass, Restoration-First Default, and Semantic Gate Bypass; each with definition, pattern, correct behavior, self-audit question, why-it-damages, prevented-by |
| mixed-case-handling.md | **L (✓)** | Compound case playbooks (grief+shubhah, authority-fatigue+textual, identity-cost+historical-criticism, inherited-filter+evidential-demand); Session 15 adds NS-11 routing note to §(v) — fideist-closed inherited-Christian background: register-hold governs before any DO, V12, or RT content; DO-14 and DO-10 both held until register shifts |
| arabic-backbone-predicates.md | **L (✓)** | C-1/2/3 (criterion), T-1/2/3 (tribunal), O-1/2/3 (ordering), K-1/2 (category); NS-6 split rows for epistemological vs. ontological burden added Session 1 |
| seven-deformations.md | **L (✓)** | Routing summary table; 7 deformations + mushābara fāsida sub-type |
| discourse-orientation.md | **L (~)** | Four orientations: truth-seek, identity-perf, autotelic, zann-mode; not directly read |
| reason-disambiguation.md | **L (~)** | Four reason-categories (sound/corrupted/pseudo-neutral/inherited); not directly read |
| foreign-premise-detection.md | **L (~)** | Detection steps; tribunal types; functional role classification; not directly read |
| modes-of-concealment.md | **L (✓)** | Five named concealment modes plus `mode-?` / `compound` IR states; Session 9 directly reads and hardens worldview-deflection / pseudo-neutrality as a live concealment-to-deployment route |
| hadith-authentication-epistemology.md | **L (✓)** | Compact canonical owner for corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed ḥadīth-authentication cases; prohibits RT-5 inflation; gates downstream doctrinal release until the transmission burden is typed. |
| inference-boundary.md | **L (~)** | Inference boundary as IR field |
| fitrah-perspectives.md | **L (~)** | Blank-slate / dual-nature fiṭrah perspectives; paired with NS-12 |
| kalamic-interlocutor.md | **L (✓)** | School identification; §Downstream Routing Table added Session 1; section-to-NS mapping in frontmatter |

### Session 5 Diagnostic and Semantic Gates

| File | Rating | Notes |
|------|--------|-------|
| prophetic-discourse-neutralization.md | **L (✓)** | Canonical owner for prophetic-discourse recontenting vs. evacuation; minimal-pair discriminator, failure tests, next-load consequences; inserted as mandatory pipeline pass before content release |
| causal-series-taxonomy.md | **L (✓)** | Canonical owner for simultaneous vs. successive series, causal regress vs. numerical infinity, circularity, and primary/secondary-cause routing; governs before generic philosophical-usurpation where the live pressure is causal-series classification |
| definition-discipline.md | **L (✓)** | Canonical owner for public-language capture, silent redefinition, universals/particulars slippage, and mental vs. extra-mental confusion; routes before M9 when the burden is broader than predication mode |
| proof-method-audit.md | **L (✓)** | Canonical owner for existence-of-God proof-family audit, hidden metaphysical load, secondary inferential status, and reminder-return discipline; includes named routing path for necessity/contingency proof-grammar overreach |
| perfection-criterion-usurpation.md | **L (✓)** | Canonical owner for imported perfection / non-eventfulness tribunal cases; minimal-pair discriminator separates tribunal, predication, composition, and speech/action-in-time pressures |
| diagnostic-ir.md | **L (✓)** | Session 5 adds `upstream_findings` plus the `semantic-discipline-required` gate; criterion import, tribunal installation, transmission demotion, semantic neutralization, and lexical-ontological traps are now auditable in the IR |
| case-state-schema.md | **L (✓)** | Session 5 adds upstream-findings discipline and semantic-gate state; preserves tribunal-plus-semantic compounds without early collapse |
| framework-pipeline.md | **L (✓)** | Session 5 adds prophetic-discourse-neutralization as a mandatory pass and blocks doctrinal dispatch while semantic-discipline work remains live; Session 9 adds the selective deployment branch note for pseudo-neutral worldview-deflection cases |
| routing-precedence.md | **L (✓)** | Session 5 adds semantic-blocker precedence (S-6) and explicit sequencing for tribunal + semantic-neutralization compounds |
| mixed-case-handling.md | **L (✓)** | Session 5 preserves cumulative build: tribunal, semantic blocker, and downstream doctrinal issue remain live in ordered sequence rather than collapsing into one label |
| foreign-premise-detection.md | **L (✓)** | Session 5 distinguishes imported criterion, tribunal installation, and transmission demotion as separate upstream findings with IR consequences |
| M9-predication-mode.md | **L (✓)** | Session 5 makes loaded negative theological terms the canonical semantic-disaggregation owner; unresolved labels now force semantic discipline before doctrinal release |
| V8-bila-kayf-anchor.md | **L (✓)** | Session 5 now hard-routes loaded negative terms through M9 first and routes imported perfection tribunal cases to perfection-criterion-usurpation.md |

### Metaphysical Architecture and Kernel

| File | Rating | Notes |
|------|--------|-------|
| metaphysical-architecture.md | **L (✓)** | Four-layer epistemic order; ontological order; what restoration means; binding to Restoration Target IR field |
| kernel-thesis.md | **L (✓)** | Five non-negotiable commitments; routing consequences; violation signatures; architecture integrity check |
| sound-reason-epistemology.md | **L (~)** | §6.2 (ḥudūth/khalq) and §6.3 (tarkīb-iftiqār) referenced as mandatory for NS-6 ontological burden cases; full content not directly read |
| prophecy-wahy-supremacy.md | **L (✓)** | Challenge patterns A/B/C; doctrinal ground for prophetic supremacy; failure tests |
| philosophical-usurpation.md | **L (✓)** | Four usurpation types; telltale features U-1 through U-5; route consequences; prohibited moves; case-state emission |
| terminology.md | **L (~)** | Arabic term glossary; not directly read |
| module-codes.md | **L (~)** | Module code registry; not directly read |

---

## §8 — Techniques and Tactics

### Techniques (V-series)

| Code | Name | Rating | Verification notes |
|------|------|--------|--------------------|
| V1 | Diagnostic (initial read) | **L (✓)** | Session 16: directly read; failure conditions (critical warning; cross-axis precedence rules); IR-visible consequences (case-state emits); minimal-pair via M5 subroutine |
| V2 | Reconstituting Reason | **L (✓)** | Session 16: exit criteria explicit; tribunal-loosened vs. frame-cleared vs. alignment-advanced discriminator; held-pending-upstream shape |
| V3 | Regress Dissolution | **L (✓)** | Session 16: structural response + equalizing move; causal-series vs. justificatory regress minimal-pair explicit |
| V4 | Contamination Identification | **L (✓)** | Session 16: bidʿī ʿaqlī vs. bidʿī naqlī minimal-pair; routes to V2 or V8 respectively |
| V5 | Directing Attention to Signs | **L (✓)** | Session 16: indication vs. argument failure condition explicit; Track a vs. Track b consciousness minimal-pair |
| V6 | Convergence | **L (✓)** | Session 16: V6 vs. E3 minimal-pair explicit; deployment rules (after dominant blocker cleared); multi-register convergence condition |
| V7 | Taqlīd Check | **L (✓)** | Session 16: V7 without V11 follow-through failure condition; routing_effects: V11-readiness prerequisite |
| V8 | Bilā Kayf Anchor | **L (✓)** | Session 16 + Session 5: M9-must-clear-first blocker; loaded-negative-term failure condition; multiple routing paths (DO-11/12/13, perfection-criterion-usurpation, V12) |
| V9 | Necessary-Knowledge Priority | **L (✓)** | Session 16: burden-reversal routing_effect; three-step execution; tawātur test as failure discriminator |
| V10 | Transmission/Content Vetting | **L (✓)** | Session 16: four branch operators; prohibited conflations per branch; provenance → contents → authority sequence mandatory |
| V11 | Taqlīd Transition | **L (✓)** | Session 16: five stages; defended-taqlīd blocker (V11 vs. V7 minimal-pair); recursive-traversal-permitted |
| V12 | Tamannaʿ Exhaustion | **L (✓)** | Session 16: five dimensions; DO-11→DO-12 stopping conditions; Advaita gap noted as M; cross-tradition scope explicit |

### Tactics

| Code | File | Rating | Session 17 verification notes |
|------|------|--------|-------------------------------|
| E1 | broadening-evidence | **L (✓)** | Failure conditions: blocks field + precedence rule section (E1 vs. doubt-vs-skepticism); NS-specific routing (NS-1, NS-2, NS-7); minimal-pair discriminator explicit |
| E2 | inferential-criterion | **L (✓)** | Session 18: failure conditions (basic-belief already operative → R1/R3; hawā/gharaḍ → F2; NS-7 irrelevant; redundant after doubt-vs-skepticism); IR consequences (routing_gate, matched_modules, held_material, output_shape); minimal-pair discriminators (E2 vs. doubt-vs-skepticism; E2 vs. R1 meta/object distinction; E2 vs. M1 universal-criterion vs. argument-structure); hold/release (single criterion-clearing move; release on criterion acknowledged or carve-out shift); anti-pattern guard (over-selection; under-sequencing without deformation axis read) |
| E3 | cumulative-case | **L (✓)** | Failure conditions: blocks field; E3 vs. V6 minimal-pair explicit ("bounded assembly within one register" vs. "cross-register convergence is itself the argument"); assembly rules |
| E4 | cross-cultural-check | **L (✓)** | Foundation/superstructure discriminator explicit; "not as appeal to numbers" deployment constraint stated in body |
| M1 | self-refutation | **L (✓)** | Staged-visibility protocol (4 stages); concealment-update failure path explicit; M1 vs. M1-P minimal-pair explicit; P7 Stop-2 governed continuation |
| M1P | performative-self-refutation | **L (✓)** | Staged-visibility protocol (4 stages); concealment-mode update on failed landing (istikbār/juḥūd/iʿrāḍ); M1P vs. M1 discriminator explicit; iʿrāḍ forbids second pass |
| M2 | prior-probability | **L (✓)** | Session 18: failure conditions (deductive vs. probabilistic form — M1/M8 governs logical arguments; grief-primary → M4; prior already surfaced → M2 complete); IR consequences (holds DO-1/DO-2/DO-4 until prior-acknowledged; prior-acknowledged flag; matched_modules expands or clears to M1/M8 if deductive); minimal-pair discriminators (M2 vs. DO-1/2/4 direct; M2 vs. M1; M2 vs. M8); hold/release (DO-1/2/4 held pending prior acknowledged; release on partial acknowledgment; do not loop); anti-pattern guard (form-of-argument mismatch on deductive arguments; register mismatch on grief-primary cases) |
| M3 | orphaned-intuition | **L (✓)** | Session 18: failure conditions (framework actually grounds deliverances — target consistent nihilist with M8; no NS read — presupposes NS-3/NS-4; performative vs. substantive commitment; hawā/gharaḍ → F2); IR consequences (orphaned-intuition upstream finding; NS-4 route opened; matched_modules adds E3 + V5 once grounding-gap acknowledged; held pending probe landing); minimal-pair discriminators (M3 vs. M8 affirmation/adversarial; M3 vs. R2 intellectual/phenomenological; M3 vs. V5 internal/external signs); hold/release (single bounded probe; hold E3/V5 until probe lands; do not loop); anti-pattern guard (false attribution to consistent framework-deniers; inversion into accusation) |
| M4 | grief-register | **L (✓)** | Philosophical argument vs. personal protest discriminator explicit; P7 Stop-1 automatic trigger; blocks field; layer-b-governed |
| M5 | deformation-triage | **L (✓)** | Critical Warning section (hardens barrier); iʿrāḍ/juḥūd boundary at M5 discriminator; pairwise sequencing table; register-hold output field; Router Guardrails |
| M6 | excluded-middle | **L (✓)** | Session 18: failure conditions (proposition poorly defined → M7 first; grief-primary → M4; iʿrāḍ concealment mode — truth-value press is absorbed; apophatic theological position on vagueness); IR consequences (truth-value-commitment active; evasion named; on failure → concealment-mode update); minimal-pair discriminators (M6 vs. M7 truth-value/definition; M6 vs. M1P excluded-middle/performative; M6 vs. doubt-vs-skepticism commitment/framework); hold/release (no content held; M7 prerequisite; do not iterate with force); anti-pattern guard (premature before M7; force-as-iteration when evasion continues) |
| M7 | definition-anchor | **L (✓)** | Scope boundary section (M7 vs. definition-discipline.md discriminator); blocks field; "local lexical dispute" vs. "broader conception-capture" explicit |
| M8 | reductio | **L (✓)** | M8 vs. M1/M1P discriminator explicit; P7 Stop-2 governance in five-step sequence; "selective recursive tactic, not autonomous chain-dump" rule |
| M9 | predication-mode | **L (✓)** | Session 5 + Session 14: directly verified; semantic-disaggregation obligations; prohibited moves; routing chain to do-attribute-precision/V8/kalamic-interlocutor |
| R1 | internalist-criterion | **L (✓)** | Session 18: failure conditions (criterion not operative → go direct to R2/R3; already accepts basic belief → R2 direct; juḥūd/istikbār concealment; hawā/gharaḍ → F2); IR consequences (criterion-challenge active; R2→R3 chain held pending R1; matched_modules includes E2 if global-internalism defense); minimal-pair discriminators (R1 vs. E2 object/meta; R1 vs. R3 criterion/experience; R1 vs. doubt-vs-skepticism criterion/framework); hold/release (R2 and R3 held pending R1; release on criterion acknowledged or theism-specific carve-out shift); anti-pattern guard (over-deployment when criterion not operative; skipping to R3 without R1) |
| R2 | the-reminder | **L (✓)** | Session 18: failure conditions (framework not cleared → recognition filtered; hawā/gharaḍ → F2; juḥūd/istikbār → relational/pastoral; recognition not near surface → F3); IR consequences (recognition-elicitation active; all argumentative content held while invitation open; recognition_strength field updated; R3 available once recognition acknowledged); minimal-pair discriminators (R2 vs. P4 single-tactic/extended-procedure; R2 vs. V5 internal/external; R2 vs. F3 eliciting-existing/creating-conditions; R2 vs. R3 phenomenological/analytical); hold/release (PRIMARY HOLD RULE — hold all argumentative content when recognition opens; release initiated by interlocutor, not by practitioner); anti-pattern guard (pressing for conclusion when recognition opens; deploying before criterion cleared) |
| R3 | warranted-basic-belief | **L (✓)** | Session 18: failure conditions (no recognition from R2 → presupposes absent material; genuine denial → F3; criterion not challenged → R1 first; DO-7 debunking raised → DO-7 + M1 before R3 can continue); IR consequences (recognition-analysis active; matched_modules adds DO-7 + M1 if debunking raised; recognition_strength advances if proper-function acknowledged; P7 Stop-2 governs); minimal-pair discriminators (R3 vs. R2 analytical/phenomenological; R3 vs. R1 inward-experience/outward-criterion; R3 vs. E2 experience-account/meta-criterion); hold/release (P7 Stop-2: one analytical move then reassess; prerequisite chain: R2 → R1 → R3); anti-pattern guard (deploying without R2 having surfaced recognition; using R3 as R2 replacement) |
| F1 | supra-vs-antirational | **L (✓)** | Session 18: failure conditions (substantive objection beneath rhetorical framing → F1 clears frame then routes to DO/RT; hawā/gharaḍ → F2; V2 needed first if reason-concept contaminated; interlocutor defending Hard Fideism themselves — different structure); IR consequences (characterization-correction active; holds R1/E3/V5 positive-case content pending supra/anti distinction established; matched_modules adds V2 if contaminated reason-concept identified); minimal-pair discriminators (F1 vs. V2 faith-characterization/reason-contamination; F1 vs. E2 characterization/criterion; F1 vs. M1 conceptual/practical self-refutation); hold/release (positive case held until distinction established; release on distinction acknowledged; must follow with substantive routing after clearing); anti-pattern guard (addressing rhetorical frame without routing to substantive objection beneath it; deploying before V2 when reason-concept contaminated) |
| F2 | volitional-dimensions | **L (✓)** | Blocks field; "hardens the barrier" failure condition explicit; intellectual vs. volitional register discriminator explicit ("Is this an intellectual objection, or is there something personally at stake?") |
| F3 | practice-epistemic-access | **L (✓)** | F2-openness as load prerequisite; seeker vs. already-believing (P5) deployment discriminator; Deployment Sequence section |
| doubt-vs-skepticism | — | **L (✓)** | Precedence rule vs. E1 explicit; two formal arguments with deployment constraints; "do not supply evidence before steps 1–4" failure condition; burden-inversion discriminator |
| husn-al-nazar-arguments | — | **L (✓)** | Blocks field; per-argument "use when/do not use when" sections; "return to fiṭrah mode after argument" rule; downstream-of-audit sequencing |
| inductive-fitri-method | — | **L (✓)** | Foundation/superstructure discriminator; DO-7 self-application section (foundation vs. superstructure from cognitive science); "not an appeal to numbers" constraint |
| symmetric-taqlid-check | — | **L (✓)** | "Practitioner's standing" failure condition explicit; V7 vs. symmetric check discriminator; epistemic-integrity constraint; layer-a-only always-on |

**Technique verification — Session 16:** V1–V12 directly read and confirmed against L standard (failure conditions, IR-visible consequences, minimal-pair discriminators). All 12 V-series entries upgraded from L(~) to L(✓). Tactic files (E/M/R/F + auxiliary) received YAML operative front matter but content was not directly read in this pass; they remained L(~).

**Tactic verification — Session 17:** All 24 tactic files directly read against L standard. 15 upgraded from L(~) to L(✓): E1, E3, E4, M1, M1P, M4, M5, M7, M8, F2, F3, doubt-vs-skepticism, husn-al-nazar-arguments, inductive-fitri-method, symmetric-taqlid-check. 8 remain L(~): E2, M2, M3, M6, R1, R2, R3, F1 — all lack explicit failure-test blocks within the file body; minimal-pair discriminators and "do not use when" conditions for these files live in the tactic INDEX only or are absent entirely. Enhanced YAML front matter (load_class, bundle, execution_phase, governs, must_precede, blocks_if_missing, trigger_conditions, operator_pack, source_status, verification_status, direct_read_verified, failure_conditions_present, ir_consequences_present, minimal_pairs_present, hold_release_rules_present, compiled_runtime_eligible, operator_pack_eligible) applied to all 23 files inspected in this pass; M9 retained its existing schema from Session 14.

**Tactic patch pass — Session 18:** All 8 remaining L(~) tactic files patched. Each file received: ##Failure Conditions, ##IR-Visible Consequences, ##Minimal-Pair Discriminators, ##Hold/Release Discipline, ##Anti-Pattern Guard. YAML verification_status updated to L_check; all _present booleans set to true. All 8 upgraded to L(✓): E2, M2, M3, M6, R1, R2, R3, F1. Tactic L(~) bucket: 0.

---

## §9 — Special Domains and Cross-Cutting Cases

| Domain | Rating | Notes |
|--------|--------|-------|
| Kalāmic school variants (Muʿtazilī / Ashʿarī / Māturīdī) | **L (✓)** | §Downstream Routing Table in kalamic-interlocutor.md; school-specific consistency rules in diagnostic-ir.md; restoration targets differentiated by school × burden; added Session 1 |
| Grief-primary cases | **C** | P7 Stop-1 governs content-withholding; M4-grief-register.md as dedicated tactic; DO-2 routes to M4; worked examples in P7-restoration-stops.md. No dedicated grief-case family with objection/response structure. Adequate for register handling; thin for content treatment when grief and DO-2 are compound |
| Compound / mixed cases | **L (✓)** | mixed-case-handling.md has six named playbooks: four original (grief+shubhah, authority-fatigue+textual, identity-cost+historical-criticism, inherited-filter+evidential-demand) + two added Session 3 audit pass: §(v) Inherited-Tradition Background + Pre-Inquiry compound — generalized Session 4 from "Christian-Background" to any inherited tradition; activation condition (1) now reads "any tradition — Christian, Jewish, secular-progressive, Hindu, or other"; tradition-specific routing note added (Christian dispatch = DO-14 → DO-10; Jewish/Hindu/secular dispatch noted as not yet having dedicated DO modules; routes through V10 Step 3 canon-authority structural form) + §(vi) Doctrinal Complexity (three structurally distinct profiles: vi-A genuine inquiry, vi-B iʿrāḍ/deflection, vi-C criterion-pressure; case-profile blocks per profile; minimal-pair discriminators) |
| Prophetic-discourse semantic neutralization | **L (✓)** | Governed by prophetic-discourse-neutralization.md; semantic recontenting and evacuation are first-class upstream findings with failure tests, minimal-pair discrimination, and pipeline priority before doctrinal content |
| Loaded negative theological terms / lexical-ontological traps | **L (✓)** | Governed canonically by M9-predication-mode.md with semantic-disaggregation obligations, prohibited moves, and routing to do-attribute-precision.md / V8 / kalamic-interlocutor.md / perfection-criterion-usurpation.md only after clarification |
| Causal-series / proof-grammar overreach | **L (✓)** | Governed by causal-series-taxonomy.md + proof-method-audit.md; messy cases involving regress, secondary-cause self-sufficiency, and necessity/contingency proof grammar now route through named owners rather than generic philosophical routing |
| Imported perfection criterion / non-eventfulness tribunal | **L (✓)** | Governed by perfection-criterion-usurpation.md with shortest-path guidance and minimal-pair separation from anthropomorphism, composition, and speech/action-in-time cases |
| Islamic-specific moral objections (fiqh ethics, penal law, gender jurisprudence) | **L (✓)** | DO-15 added Session 15 (Gap 4 closed). Full entry in do-second-loop.md: Type D usurpation + V2 + FPD mandatory before content; Level A / Level B moral-claim distinction; four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma); conditions-application analysis; NS-8/NS-4 pairing; M4 gate for affective register |
| Final-prophethood challenges — transmission layer | **L (✓)** | RT-1 through RT-4 in revelation-transmission.md |
| Final-prophethood challenges — moral-luck layer | **L (✓)** | DO-8 (Prophetic Mission and Moral Luck) in do-second-loop.md; failure test added Session 15 |
| Final-prophethood challenges — prophetic authority vs. philosophy | **L (✓)** | prophecy-wahy-supremacy.md (challenge patterns A/B/C) |
| Comparative religion — Christianity | **L (✓)** | DO-11/DO-12/DO-13/DO-14 in do-christian-extensions.md; philosophical-usurpation.md Type A/B. DO-14 (added Session 3) governs Christian canon-selection confusion (which Bible version; Protestant/Catholic/Orthodox canonical diversity; authority-of-scripture-within-Christianity); case-profile block; three sub-question discrimination; criterion-gap opening to DO-10 |
| Comparative religion — cross-tradition via family transfer | **C** | Cases from any tradition that instantiate a governed family are covered through that family. Specific transfer routes: divine-multiplicity configurations (polytheism, henotheism, Hindu monistic/pluralistic-deity arrangements, apatheism) → V12 (tamannaʿ exhaustion; SKILL.md explicitly marks this as "any interlocutor" before DO-11/13 Christian overlay) + Creator-creation distinction in metaphysical-architecture.md; devotional-disorder (desire-as-worship, idolatry as fiṭrah-substitution) → hawā + ʿāda deformation types + F2 (volitional dimensions); cross-tradition philosophical-framework usurpation (Advaita non-dualism, Buddhist impermanence framework, Confucian naturalism as arbiter) → philosophical-usurpation.md Types A–D; religious-diversity objection → DO-4; noetic-structure diagnosis → NS-1 through NS-12 (no religious-background restriction). These transfer routes are operative architecture, not generic fallback. |
| Comparative religion — bespoke religion-specific families (Buddhist anatta / impermanence challenge to Islamic soul-doctrine; Hindu non-dualist Advaita as rival theological ontology; Jewish final-prophethood argument) | **M** | No dedicated DO-series case files. Cases whose argument structure requires religion-specific doctrinal content (not merely family-transfer engagement) have no canonical owner. Adherents of these traditions whose cases instantiate a governed family are engaged through that family — this entry captures only the bespoke argument-structure gap. |
| Conversation excerpt handling — thin-basis discipline | **L (✓)** | Gap 1 closed Session 15. noetic-reading-checklist.md §"Thin-Basis / Excerpt Mode" now has structured minimum-basis rule: three-dimension convergence (Dimensions 1/4/8) required before confident NS emission; provisional-fields list; mandatory decisive-missing-differentiator; failure test |
| Ḥadīth corpus transmission and authentication epistemology | **L** | `hadith-authentication-epistemology.md` now governs corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed downstream misuse; V10 remains the shared provenance -> contents -> authority technique; RT-1 through RT-4 remain Qurʾānic/scriptural rather than ḥadīth codes |
| Sufism-related crises (contested practices, ṭarīqah authority claims) | **M** | Not governed; not referenced in SKILL.md activation scope but may arise in Muslim-internal cases |

---

## §10 — Gap Inventory (Partial and Missing Families)

The following are the actionable gaps in priority order based on scope-claim vs. governed-coverage distance:

### Resolved Check 1 — Conversation Excerpt Thin-Basis Discipline (Gap 1 closed Session 15)
**Claimed:** SKILL.md activation trigger includes "conversation excerpts."
**Governed:** P7 Stop-4 (underdetermined case); "Excerpt Over-Read" anti-pattern (anti-patterns.md); noetic-reading-checklist.md §"Thin-Basis / Excerpt Mode" now contains: (a) minimum-basis rule — three-dimension convergence requirement (Dimensions 1, 4, 8) before confident NS emission; (b) fields that must remain provisional until basis is confirmed (NS code, deformation type, concealment mode, discourse orientation); (c) mandatory decisive-missing-differentiator field population when excerpt is thin; (d) explicit failure test.
**Residual risk:** Low. The proactive gate at the read-attempt level now closes the loop that Stop-4 and the anti-pattern left open.

### Resolved Check 2 — Register-Hold Bypass Failure Detection
**Claimed:** The concealment × orientation matrix in case-state-schema.md governs content deployability at Gate Check 6.
**Governed:** The matrix is explicit and the named anti-pattern exists in anti-patterns.md. The failure signature and the governing matrix now point to each other cleanly.
**Residual risk:** Low — the remaining risk is operator discipline, not owner ambiguity.
**Regression check:** Keep the matrix cell and anti-pattern aligned whenever either file changes.

### Resolved Check 3 — DO-Core and DO-Second-Loop Failure Tests (Gap 3 closed Session 15)
**Claimed:** DO-1 through DO-10 are L.
**Governed:** Failure-test blocks added to DO-3 through DO-10 in Session 15 direct-read pass. Each entry now has a "Failure test" subsection specifying named failure signatures, discrimination requirements, and sequencing obligations. DO-1 through DO-10 are now all L (✓).
**Residual risk:** Low. Remaining verification gap (V-series and tactics direct-read) is tracked in TODO.md as a lower-priority item.

### Resolved Check 4 — Islamic-Specific Moral Objections (Gap 4 closed Session 15)
**Claimed:** NS-8 profile covers moral-recoil component; Type D philosophical usurpation covers liberal-political-philosophy-as-moral-arbiter.
**Governed:** DO-15 (Islamic-Specific Moral Objections) added to do-second-loop.md. Full entry includes: FPD + Type D usurpation identification mandatory before content; Level A / Level B moral-claim distinction (fiṭrī universal recognitions vs. system-specific philosophical conclusions); four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma) as internal operative standard; conditions-application analysis for ḥudūd and historical slavery; M4 affective-register gate for NS-8 cases; named collapse-move failure tests; NS-8/NS-4 pairing.
**Residual risk:** Low. Specific juristic sub-analysis (individual fiqh chapter detail) remains outside this repo's scope — the architecture governs the criterion, the operative distinctions, and the response shape, not a complete fiqh manual.

### Gap 5 — Comparative Religion: Bespoke Religion-Specific Families (M, correctly bounded)
**What is governed:** The repo governs comparative-religion cases at two levels that must not be conflated. (1) Explicit Christian extensions: DO-11/DO-12/DO-13 in do-christian-extensions.md. (2) Cross-tradition family-transfer coverage: any case from any tradition that instantiates a governed family is covered through that family — specifically: divine-multiplicity (polytheism, henotheism, Hindu monistic/pluralistic-deity, apatheism) via V12 + Creator-creation distinction; devotional-disorder (desire-as-worship, idolatry) via hawā/ʿāda deformation + F2; cross-tradition philosophical-framework usurpation via philosophical-usurpation.md Types A–D; religious-diversity via DO-4; noetic-structure diagnosis via NS-1 through NS-12. These are operative architecture, not generic fallback.
**What is not governed:** Bespoke argument structures that require religion-specific doctrinal content and cannot be resolved through family transfer: (a) Buddhist anatta/no-soul as a direct challenge to the Islamic account of the nafs; (b) Hindu non-dualist (Advaita Vedanta) claim as a rival theological ontology; (c) Jewish final-prophethood arguments grounded in Torah's self-characterization as complete; (d) Buddhist impermanence framework as a rival account of creation and divine constancy. These remain M.
**Risk:** Conflating the two levels — treating "no bespoke file exists" as "no coverage exists" — causes the practitioner to misrepresent the repo's reach and may suppress correct routing through family transfer for a Hindu or Buddhist interlocutor whose case actually does instantiate a governed family.
**Remediation:** SKILL.md and coverage-ledger corrected to distinguish both levels. Bespoke-family gap remains; remediation requires dedicated case content, not a description fix.

### Resolved Check 6 — Ḥadīth Transmission and Authentication Epistemology
**Claimed:** "transmission and final-prophethood challenges" in SKILL.md.
**Governed:** `hadith-authentication-epistemology.md` now provides a compact canonical owner for corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed doctrinal misuse; V10 remains the shared provenance -> contents -> authority technique; `revelation-transmission.md` stays scoped to RT-1 through RT-4 instead of carrying ḥadīth as an interim overlay.
**Residual risk:** Low. The remaining non-goal is a full ḥadīth-science encyclopedia. This repo now governs the routing and release discipline the gap required without attempting a full specialist manual.

### Gap 7 — Mode-of-Concealment File (unverified)
**Claimed:** Modes of concealment are L based on cross-reference.
**Verified:** modes-of-concealment.md exists; content not directly read.
**Risk:** Low — the IR schema fields and routing-precedence references make it structurally implausible that this file is absent — but the content has not been directly audited for failure conditions or self-audit questions.
**Remediation:** Add to next direct-read pass.

---

## §11 — Audit Confidence Summary

| Confidence level | Count | Notes |
|-----------------|-------|-------|
| **L (✓)** — directly read and confirmed | 97 entries | Session 15 upgrades: DO-3–DO-6, DO-7–DO-10, DO-15, noetic-reading-checklist.md, mixed-case-handling.md. Session 16 upgrades: V1–V12. Session 17 upgrades: E1, E3, E4, M1, M1P, M4, M5, M7, M8, F2, F3, doubt-vs-skepticism, husn-al-nazar-arguments, inductive-fitri-method, symmetric-taqlid-check (15 tactics). Session 18 upgrades: E2, M2, M3, M6, R1, R2, R3, F1 (8 tactics — all remaining L(~) tactic files) |
| **L (~)** — confirmed by cross-reference | ~21 non-tactic entries | Tactic bucket: 0 (all resolved Session 18). Remaining L(~): procedures P1–P5 (5); NS profiles NS-2/3/4/5/7/8/9/11/12 (9); governance files discourse-orientation, reason-disambiguation, inference-boundary, fitrah-perspectives, sound-reason-epistemology, terminology, module-codes (7). Total approximate: ~21 non-tactic entries remain cross-reference only |
| **P** — partial (identified gap) | 0 entries | All tracked P items closed in Session 15 (Gap 1, Gap 3, Gap 4) |
| **M** — missing/implied | 2 entries | Bespoke religion-specific families and Sufism-related crises |

**Total governed families/files:** ~108 entries across NS, DO, RT, deformations, concealment, governance procedures, techniques, semantic gates, pattern profiling, and special domains (DO-15 added).

**Claimed but not fully governed (net):** 2 missing (bespoke religion-specific families, Sufism — both tracked in TODO.md as Needs Human Review). All P items closed this session. Transmission claims remain accurate for Qurʾānic scope; ḥadīth authentication governed separately from the RT family.

---

## §13 — Canonical Owner Map

This map distinguishes three functional roles files play in the architecture. Each file has exactly one primary role; some files serve secondary roles where noted.

| Role | Definition | Files |
|------|------------|-------|
| **Routing** | The file's primary job is to direct the practitioner to the correct next file, module, or instrument. It does not supply response content. | `case-library/INDEX.md`, `case-library/profiles/INDEX.md`, `references/diagnostics/INDEX.md`, `references/tactics/INDEX.md`, `references/techniques/INDEX.md`, `references/procedures/INDEX.md`, `references/diagnostics/framework-pipeline.md`, `references/diagnostics/routing-precedence.md`, `case-library/noetic-profiles.md` (redirect-only) |
| **Diagnostic** | The file's primary job is to classify the case — the noetic state, deformation type, concealment mode, discourse orientation, claim-level, pattern-profile, reason-category, foreign-premise status, or semantic blocker family. It produces typed state that feeds the IR. | `V1-diagnostic.md`, `noetic-reading-checklist.md`, `seven-deformations.md`, `modes-of-concealment.md`, `discourse-orientation.md`, `reason-disambiguation.md`, `pattern-profiling.md`, `foreign-premise-detection.md`, `arabic-backbone-predicates.md`, `diagnostic-ir.md`, `case-state-schema.md`, `mixed-case-handling.md`, `kalamic-interlocutor.md`, `fitrah-perspectives.md`, `prophetic-discourse-neutralization.md`, `causal-series-taxonomy.md`, `definition-discipline.md`, `proof-method-audit.md`, `perfection-criterion-usurpation.md` |
| **Restoration substance** | The file's primary job is to supply the doctrinal, epistemic, or ontological content that constitutes the actual response — what is being restored and how. | `metaphysical-architecture.md`, `kernel-thesis.md`, `sound-reason-epistemology.md`, `prophecy-wahy-supremacy.md`, `philosophical-usurpation.md`, `terminology.md`, all NS profile files (`ns-1` through `ns-12`), all DO files (`do-core.md`, `do-second-loop.md`, `do-christian-extensions.md`, `do-attribute-precision.md`), `revelation-transmission.md`, all V-series technique files (`V2` through `V12`), all tactic files (`E1–E4`, `M1–M9`, `R1–R3`, `F1–F3`), all procedure files (`P1–P7`) |
| **Bridge** | The file serves a mixed role: it participates in routing AND supplies restoration substance. Bridge files are the highest-risk for over-loading — loading them when only one of their roles is needed brings in unnecessary content. | `kalamic-interlocutor.md` (diagnostic + Māturīdī/Ashʿarī/Muʿtazilī restoration substance), `do-attribute-precision.md` (routing precision fixtures + restoration substance), `anti-patterns.md` (self-audit routing + failure detection), `heuristics.md` (always-active background + restoration mode) |
| **Governance** | The file's primary job is to constrain what the practitioner may do at a routing or content level — hard rails, stop conditions, prohibition enforcement, consistency checks. | `P7-restoration-stops.md`, `routing-precedence.md`, `diagnostic-ir.md` (also diagnostic), `anti-patterns.md` (also bridge), `inference-boundary.md`, `kernel-thesis.md` (also restoration substance) |

**Owner map rules:**
1. Do not load a routing file expecting it to supply response content — it will not.
2. Do not use a restoration-substance file to make a routing decision — routing is in the routing and diagnostic files.
3. Bridge files must be loaded for a specific declared need (either their routing function or their substance function) — do not load them because they contain something relevant to both; the load condition in the frontmatter specifies when each function applies.
4. Governance files govern regardless of whether they are explicitly cited — P7 stops fire when triggered even if P7-restoration-stops.md is not in the active load set.

---

## §12 — Revision Log

| Date | Scope | Changes |
|------|-------|---------|
| 2024-12 Session 1 | Kalāmic variance pass | NS-6 school identification, NS-10 burden check, §Downstream Routing Table in kalamic-interlocutor.md, IR consistency rules, backbone predicate split rows, do-attribute-precision.md frontmatter update |
| 2025-01 Session 2 | Parity ledger creation + governance hardening | This file created; gaps identified; case-state-schema.md matrix rating corrected from P to L after direct read; SKILL.md description truthfulness pass (comparative-religion coverage distinguished at two levels: explicit Christian extensions + cross-tradition family-transfer; bespoke religion-specific gaps named; hadith authentication gap named); comparative-religion §9 entry split into C (family-transfer) and M (bespoke religion-specific); Gap 5 rewritten to distinguish the two levels; revelation-transmission.md scope boundary added; canonical owner map added (§13); anti-patterns.md: 2 new anti-patterns added (Excerpt Over-Read, Register-Hold Bypass); kalamic-interlocutor.md: Ashʿarī communal-obligation section added with lever rule, substrate-load discipline, failure language |
| 2026-04 Session 3 | Pattern-family robustness + multi-module routing discipline audit + profile-patterning patch set | pattern-family-audit.md: 8-deliverable audit document created (pattern-family map PF-1 through PF-12; coverage/ownership audit; routing/cumulative-dispatch audit; abstraction-level audit; ranked gap list GAP-A through GAP-I; file-by-file patch plan; regression fixture suite F1–F8; production-readiness judgment). Patches implemented: (A) do-christian-extensions.md — DO-14 added (Christian Canon Selection Confusion; case-profile block; three sub-question discrimination; criterion-gap opening; prohibited moves; NS pairing); (B) mixed-case-handling.md §(vi) — Doctrinal Complexity three-profile playbook added (vi-A inquiry, vi-B deflection/iʿrāḍ, vi-C criterion-pressure; case-profile blocks; minimal-pair discriminators); (C) mixed-case-handling.md §(v) — Inherited Christian Framework + Pre-Inquiry compound playbook added (case-profile routing rule, not surface-pattern trigger; regression-repair for restoration-first, Christology-preemption, RT-2 collapse, criterion-grant failure modes; FPD gate; sub-question discrimination; pass/fail checks for four named failures); (D) V12-tamanuc-exhaustion.md — cross-tradition scope statement added (structural trigger, not tradition-specific; Advaita gap noted); DO-11→DO-12 stopping conditions added (sequential only; P-3 violation named; authority-shift → V10+RT-2 redirect); (E) do-second-loop.md — Comparative-Prophethood Opening-Frame Dispatch section added (DO-10 → DO-4 → prophecy-wahy-supremacy.md sequence with structural dependency; stopping conditions across levels; case-profile block); (F) philosophical-usurpation.md — cross-tradition scope added to frontmatter so the family-transfer rule is owner-local and auditable (types keyed to framework, not interlocutor background); (G) revelation-transmission.md — Interim Hadith-Transmission Routing section added (three case-profile forms: isnād skepticism, āḥād epistemology, historical-critical import; instruments that apply; explicit architecture-end statement); V1-diagnostic.md — specialty-marker list updated (DO-14 added; hadith interim routing noted; exhaustive-vs-illustrative clarification added); coverage-ledger §2 DO-14 row added; §9 comparative-religion row updated; Gap 4 remediation note (DO-14 used for Christian canon, not Islamic ethics; next code = DO-15); Gap 6 upgraded from M to partial C; this revision log row added |
| 2026-04 Session 4 | Generalize-upward pass — tests, distinctions, and routing logic lifted to highest valid structural level | Four patches implemented: (H1) V10-transmission-content-vetting.md — `> scope:` cross-tradition statement added to frontmatter; "Recognition vs. creation principle (cross-traditional)" named and placed in Step 3; "Canon-authority structural form (cross-traditional)" block added in Step 3 with criterion-circularity structure named across Protestant/Catholic/Jewish/Hindu traditions; Branch B "Route after" updated to include DO-14 for Christian authorization cases. V10 is now the generalized structural owner of the canon-authority-criterion level; tradition-specific branch operators remain. (H2) mixed-case-handling.md §(v) — title generalized from "Christian-Background Pre-Inquiry" to "Inherited-Tradition Background — Pre-Inquiry Compound"; activation condition (1) generalized from "Christian tradition, any denomination" to "any tradition — Christian, Jewish, secular-progressive, Hindu, or other"; feature (3) generalized from Christian-specific module list to structural description; tradition-specific routing note added (Christian dispatch = DO-14 → DO-10; Jewish/Hindu = V10 Step 3 structural form + no dedicated DO module yet; secular = Type B usurpation). (H3) do-christian-extensions.md DO-14 sub-question (c) — structural pointer added: "the criterion-circularity form of this sub-question is cross-traditional; V10 Step 3 §(Canon-authority structural form) is the generalized structural owner; DO-14 is its Christian instantiation." (H4) coverage-ledger.md — §3 V10 routing note extended; §9 compound/mixed cases row updated to reflect §(v) generalization; this revision log row added. What remained tradition-specific: DO-14's three sub-question structure and the specific Protestant/Catholic/Orthodox corpora, formation events, and authorization arguments; §(v)'s Christian-specific dispatch table (DO-14 → DO-10 → DO-11/12); V10 Branch A (Qurʾān-specific transmission conditions); V10 Branch B (Biblical manuscript conditions); V10 Branch C (Hadith isnād conditions). No fake universals created: Jewish/Hindu authority-certification cases are routed to V10 Step 3 structural form with explicit "no dedicated DO module yet" notation. |
| 2026-04 Session 5 | Volume 1–4 semantic-gate and owner-hardening pass | New canonical diagnostic owners landed: prophetic-discourse-neutralization.md (semantic recontenting vs. evacuation), causal-series-taxonomy.md, definition-discipline.md, proof-method-audit.md, perfection-criterion-usurpation.md. Shared governance hardened: diagnostic-ir.md and case-state-schema.md now carry upstream findings plus `semantic-discipline-required`; framework-pipeline.md adds prophetic-discourse-neutralization before content release; routing-precedence.md and mixed-case-handling.md preserve ordered sequencing for tribunal + semantic blocker compounds; foreign-premise-detection.md now distinguishes criterion import, tribunal installation, and transmission demotion. Semantic routing hardened: M9-predication-mode.md now canonically owns loaded negative theological terms; V8 hard-routes such terms through M9 first; do-attribute-precision.md and kalamic-interlocutor.md updated to require semantic disaggregation before doctrinal release. Branding cleanup performed in do-core.md, do-second-loop.md, do-christian-extensions.md, sound-reason-epistemology.md, terminology.md, fitrah-perspectives.md, ns-8-muslim-internal-crisis.md, case-library/INDEX.md, and this ledger. |
| 2026-04 Session 6 | Integrative grokking pass | New operational owner landed: pattern-profiling.md, separating live `claim_level` / `pattern_profile` emission from the historical pattern-family audit. Core governance aligned: case-state-schema.md, diagnostic-ir.md, diagnostic-ir.schema.json, framework-pipeline.md, routing-precedence.md, mixed-case-handling.md, noetic-reading-checklist.md, module-codes.md, SKILL.md, and README.md now surface higher-order burdens explicitly and route them before first-order case content. Ledger drift corrected: Register-Hold Bypass contradiction removed; anti-pattern count updated; case-library/INDEX.md now includes DO-14 in live routing. Terminology normalized around upstream-tribunal language and the secondary restorative route. |
| 2026-04 Session 7 | Corrective verification pass | Restored live mixed-case playbooks (v) inherited-tradition/pre-inquiry compound and (vi) doctrinal-complexity routing; relaxed `claim_level` from always-required surfaced output to conditional higher-order emission while preserving IR gating; fixed stale DO-14 and P-D routing references; added owner-local guards for perfection-criterion, causal-impossibility, loaded-term, source-native-foundation, and hadith/transmission boundary drift; marked production-hardening-audit.md as historical non-governing substrate. |
| 2026-04 Session 8 | Known-good governance restoration pass | Restored two-layer output contract in SKILL.md; restored current-pass `matched_modules` and IR-owned `output_shape` / `p7_stops_active` / withheld-content discipline; restored `hadith-authentication-epistemology.md` plus routing hooks in diagnostics index, module catalogue, V10, revelation-transmission, module-codes, routing-precedence, pattern-profiling, and case-library index; kept later cumulative/restoration and semantic-gate improvements intact. |
| 2026-04 Session 9 | Selective worldview-deflection restoration pass | Restored the dedicated P6 section for worldview-deflection / pseudo-neutrality; restored the exact "I have no religion, I just follow the evidence wherever it leads" regression fixture in pattern-family-audit.md; hardened modes-of-concealment.md, noetic-reading-checklist.md, framework-pipeline.md, and SKILL.md so pseudo-neutral slogans are handled as first-class selective DSL-IR routing with full internal diagnosis plus bounded externalization, rather than as generic objection-answering. |
| 2026-04 Session 16 | Operative front matter rollout + V-series direct-read verification (v0.2.0.0) | Operative YAML front matter added to all remaining module classes: diagnostic (6 files: causal-series-taxonomy, definition-discipline, hadith-authentication-epistemology, perfection-criterion-usurpation, proof-method-audit, prophetic-discourse-neutralization); case-library (18 files: do-core, do-second-loop, do-christian-extensions, noetic-profiles, philosophical-usurpation, revelation-transmission, ns-1 through ns-12); governance (25+ files: framework-pipeline, diagnostic-ir, anti-patterns, case-state-schema, noetic-reading-checklist, mixed-case-handling, output-release, diagnostic-render-contract, seven-deformations, modes-of-concealment, discourse-orientation, reason-disambiguation, foreign-premise-detection, arabic-backbone-predicates, kalamic-interlocutor, pattern-profiling, fitrah-perspectives, inference-boundary, operative-contracts, pattern-family-audit, coverage-ledger, metaphysical-architecture, prophecy-wahy-supremacy, kernel-thesis, module-codes, sound-reason-epistemology, terminology, and all INDEX files). Total: ~99 files changed. V-series direct-read verification: V1–V12 all directly read against L standard (failure conditions, IR-visible consequences, minimal-pair discriminators); all 12 upgraded from L(~) to L(✓). §9 stale entries fixed: conversation excerpt handling upgraded P → L(✓), DO-8 §9 entry upgraded L(~) → L(✓). |
| 2026-04 Session 17 | Tactic direct-read verification + enhanced YAML front matter rollout (v0.2.0.0) | All 24 tactic files directly read against L standard (failure conditions, IR-visible consequences, minimal-pair discriminators, routing/trigger conditions, hold/release constraints). 15 upgraded from L(~) to L(✓): E1, E3, E4, M1, M1P, M4, M5, M7, M8, F2, F3, doubt-vs-skepticism, husn-al-nazar-arguments, inductive-fitri-method, symmetric-taqlid-check. 8 remain L(~): E2 (no failure test; minimal-pair in INDEX only), M2 (no failure test; no explicit failure for skipping), M3 (no failure test; no tactic-level discriminator), M6 (no failure test; conditions in INDEX only), R1 (no failure test; no E2 vs. R1 discriminator), R2 (no failure test; framework-cleared condition in INDEX only), R3 (no failure test; sequencing note present but not standalone discriminator), F1 (no failure test; "bad arguments not supra/anti" condition in INDEX only). Enhanced YAML schema applied to all 23 inspected files: load_class, bundle, execution_phase, governs, must_precede, blocks_if_missing, trigger_conditions, operator_pack, source_status, verification_status, direct_read_verified, failure_conditions_present, ir_consequences_present, minimal_pairs_present, hold_release_rules_present, compiled_runtime_eligible, operator_pack_eligible. M9 retained existing schema from Session 14. §8 tactics table expanded to per-file format. §11 confidence summary updated: L(✓) 74 → 89; tactic L(~) ~24 → 8. TODO.md "Tactic direct-read verification" moved to Resolved. tools/check_frontmatter.py validation script created. |
| 2026-04 Session 18 | Tactic patch pass — remaining L(~) tactic files (v0.2.0.0) | All 8 remaining L(~) tactic files patched in-body: E2 (inferential-criterion), M2 (prior-probability), M3 (orphaned-intuition), M6 (excluded-middle), R1 (internalist-criterion), R2 (the-reminder), R3 (warranted-basic-belief), F1 (supra-vs-antirational). Each file received explicit §Failure Conditions (when not to deploy; how the tactic fails; what happens next), §IR-Visible Consequences (routing_gate effects, matched_modules, held_material, output_shape, per-outcome state transitions), §Minimal-Pair Discriminators (deployment-level discrimination from nearest neighbor tactics), §Hold/Release Discipline (what is held, what the release signal is, do-not-loop rule), §Anti-Pattern Guard (principal misuse risk with mechanism). YAML: verification_status upgraded to L_check; direct_read_verified: true; all _present booleans set to true. §8 per-file notes updated. §11 L(✓) count updated 89 → 97; tactic L(~) bucket updated 8 → 0. tools/check_frontmatter.py: PASS (0 errors, 103 files). |
| 2026-04 Session 15 | Artifact consolidation and gap-filling pass (v0.2.0.0) | Root TODO.md created as single canonical future-work location (consolidates all gaps from coverage-ledger.md §10 and pattern-family-audit.md). Gap 1 closed: noetic-reading-checklist.md §"Thin-Basis / Excerpt Mode" replaced with structured minimum-basis rule — three-dimension convergence requirement (Dimensions 1/4/8), provisional-fields list, mandatory decisive-missing-differentiator, failure test. GAP-H closed: mixed-case-handling.md §(v) NS-11 routing note added — fideist-closed inherited-Christian posture triggers register-hold before any DO, V12, or RT content. Gap 3 closed: failure-test blocks added to DO-3, DO-4, DO-5, DO-6 in do-core.md and DO-7, DO-8, DO-9, DO-10 in do-second-loop.md; all entries now L (✓). Gap 4 closed: DO-15 (Islamic-Specific Moral Objections / Imported-Criterion Form) added to do-second-loop.md — FPD + Type D usurpation + V2 mandatory sequencing; Level A / Level B moral-claim distinction; four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma) as internal operative standard; conditions-application analysis for ḥudūd and historical slavery; M4 affective-register gate; collapse-move failure tests; NS-8/NS-4 pairing. do-second-loop.md header updated to DO-7 through DO-15; fan-out table updated with moral-criterion usurpation row. coverage-ledger.md §2 DO table, §4 Type D gap, §9 Islamic-specific moral objections, §10 gaps 1/3/4, §11 confidence summary all updated. |
