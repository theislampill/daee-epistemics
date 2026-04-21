> role: parity/coverage audit ledger — explicit fidelity ratings for every recognized family and procedure in the skill; canonical source for distinguishing "already landed," "compressed but governed," "partial," and "missing/implied"
> use when: auditing whether a claim in SKILL.md, README, or a routing table is actually backed by governed content; updating after an edit pass; deciding which gap to close next
> do not use when: routing a live case — this file does not route; it describes what the routing apparatus covers and at what fidelity
> revision protocol: update the `last-audited` field and the affected row(s) after any edit pass; do not let the ledger go stale by making edits without updating it
> release-state note: this ledger describes the live workspace baseline for the current pass. Local workspace artifacts such as `production-hardening-audit.md` remain non-governing unless tracked in git.
> current-pass note: 2026-04 selective-routing hardening and release-packaging fidelity pass — tightened current-pass activation discipline, strengthened hold/stop enforcement without deleting Layer A diagnosis, preserved concealment-sensitive Layer A / Layer B behavior, and corrected release-facing packaging guidance to prefer slash-safe Bash / WSL / Linux archive generation
> last-audited: 2024-12 (Session 1 — kalamic variance pass) + 2025-01 (Session 2 — parity ledger creation) + 2026-04 (Session 3 — pattern-family robustness audit + profile-patterning patch set) + 2026-04 (Session 4 — generalize-upward pass) + 2026-04 (Session 5 — semantic-gate and owner-hardening pass for Volumes 1–4) + 2026-04 (Session 6 — integrative grokking pass) + 2026-04 (Session 7 — corrective verification pass) + 2026-04 (Session 8 — narrow parity / truthfulness / governance-surface hardening pass) + 2026-04 (Session 9 — readiness / grokking hardening pass) + 2026-04 (Session 10 — commit-parity hardening pass) + 2026-04 (Session 11 — hadith-transmission and authentication hardening pass) + 2026-04 (Session 12 — v0.1.0.0 release truthfulness / packaging pass) + 2026-04 (Session 13 — concealment-hardening and output-layer separation pass) + 2026-04 (Session 14 — selective-routing hardening and release-packaging fidelity pass)

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

## §2 — Doctrinal Objections Family (DO-1 through DO-14)

### DO-1 through DO-6 (do-core.md)

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-1 | Divine Hiddenness | **L (✓)** | Objection stated strongly, strongest rebuttal, operative response, remaining probe; P4 (maieutic) routing when search-narrative is live |
| DO-2 | Evidential Evil | **L (✓)** | Skeptical-theism rebuttal addressed; M4 routing when grief-primary; distinction between logical and evidential problem present |
| DO-3 | Evolutionary Debunking | **L (~)** | Quick DO table routing confirmed; content depth unverified by direct read |
| DO-4 | Religious Diversity | **L (~)** | Foundation/superstructure distinction present per Quick DO table |
| DO-5 | Transcendence and Language | **L (~)** | V8 primary instrument; minimal-pair discriminator vs. DO-13 in `do-christian-extensions.md` (✓) |
| DO-6 | Attribute Coherence | **L (~)** | V8 + dhat/fiʿl distinction per Quick DO table |

**Failure-condition audit note:** do-core.md has a strong objection/rebuttal/operative-response structure for DO-1 and DO-2 (confirmed). DO-3 through DO-6 were directly read in Session 5 for terminology cleanup and routing review; explicit failure tests still remain thin enough to justify a future targeted audit.

### DO-7 through DO-10 (do-second-loop.md)

| DO code | Objection | Rating | Notes |
|---------|-----------|--------|-------|
| DO-7 | Cognitive Science of Religion / HADD | **L (~)** | M1 or V9 per Quick DO table; content depth unverified by direct read |
| DO-8 | Prophetic Mission and Moral Luck | **L (~)** | Hujjah principle per Quick DO table |
| DO-9 | Great Pumpkin | **L (~)** | Universality condition + tawātur fiṭrī per Quick DO table |
| DO-10 | Three-Tiered Epistemological Structure | **L (~)** | fiṭrah → khabar → naẓar ordering; V9 when ḍarūrī is attacked; Quick DO table routing |

**Failure-condition audit note:** do-second-loop.md was directly read in Session 5 for terminology cleanup and routing review. The objection/response structure is present, but explicit failure-test blocks remain thin enough to justify a future targeted audit.

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

**Scope boundary:** RT family still covers Qurʾānic/scriptural transmission specifically. Hadith corpus/authentication epistemology is now governed separately by `hadith-authentication-epistemology.md`, while Old/New Testament transmission in comparative Islamic perspective and the non-Qurʾānic sunnah preservation question as a full specialist case family remain outside the RT owner itself.

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

**Case-state emission format:** Typed block with type, telltale features, framework name, functional role, step, prohibited-move flag. **L (✓)**.

**Gap (Type D):** The moral-arbitration case under Type D is structurally landed as a usurpation type, but the content depth for specific Islamic jurisprudential ethics objections (e.g., corporal punishment, gender jurisprudence) is not worked through at the DO-series level. Type D identifies the usurpation and routes to NS-8 and seven-deformations.md, but no dedicated DO code covers "Islamic-specific moral objections" with a full operative-response structure. This is the moral-recoil gap noted in NS-8. See §10.

---

## §5 — Deformation Types (Seven Deformations)

| Deformation | Rating | Notes |
|-------------|--------|-------|
| Iʿtiqādāt mawrūtha (inherited beliefs) | **L (✓)** | Primary cue, first move, common confusion; V2 primary |
| Mushābara fāsida (1-A) — sub-type | **L (✓)** | Named sub-variant of iʿtiqādāt mawrūtha; distinguishing marker: one premise regenerates downstream conclusions even after local clearing; M1 applied to the premise itself |
| Hawā (volitional desire) | **L (✓)** | F2 or relational engagement; objections multiplying after clearing is the diagnostic signal |
| Ẓann (conjecture, unexamined assumption) | **L (✓)** | V7 (symmetric critique of taqlīd); distinguished from genuine shubhah |
| Taqlīd (imitation) | **L (✓)** | Tahqiq invitation; distinguished from ẓann |
| ʿĀda (habituation) | **L (✓)** | V2 then V5; distinguished from iʿtiqādāt mawrūtha by phenomenology (distortion feels like direct reality) |
| Gharaḍ (interest/cost of inquiry) | **L (✓)** | F2; distinguished from hawā by the honesty of the inquiry being what is costly |
| Shubha (genuine intellectual obstacle) | **L (✓)** | The one deformation that responds to intellectual engagement; V9 or matched case response; over-attribution to this deformation is the primary diagnostic error |

**Note on count:** The routing table has 8 rows for 7 deformations — mushābara fāsida (1-A) is a sub-type of iʿtiqādāt mawrūtha, not an eighth deformation. Both the count (7) and the sub-type (1-A) are correctly present in seven-deformations.md.

**Routing summary table:** Present in seven-deformations.md with primary cue, first move, prohibited first move, common confusion. **L (✓)**.

---

## §6 — Modes of Concealment

| Mode | Rating | Notes |
|------|--------|-------|
| Irāḍ (turning away) | **L (~)** | modes-of-concealment.md; referenced in IR concealment field |
| Juḥūd (denial despite recognition) | **L (~)** | modes-of-concealment.md |
| Inkār (rejection) | **L (~)** | modes-of-concealment.md |
| Istikbār (arrogance) | **L (~)** | modes-of-concealment.md |
| Nifāq (hypocrisy/insincerity) | **L (~)** | modes-of-concealment.md |
| clear (resolved absence of active concealment) | **L (~)** | IR and case-state valid value when concealment is positively resolved as non-operative |
| mode-? (indeterminate) | **L (~)** | IR valid value when mode cannot be confirmed |
| compound | **L (~)** | IR valid value for mixed concealment |

**modes-of-concealment.md** not directly read in this pass; confirmed by systematic presence in IR schema and routing-precedence.md references. Verify full content in next pass.

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
| P6 — Universal ʿAqīdah Principle | **L (~)** | Dedicated file; NS-8 compound cases |
| P7 — Restoration Stops | **L (✓)** | Five named stops with triggers, mandatory actions, prohibited actions, exit criteria, re-entry conditions |

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
| framework-pipeline.md | **L (✓)** | Structural branching chart; paired with routing-precedence and diagnostic-ir; explicitly names conditional higher-order emission and audit companions. |
| case-state-schema.md | **L (✓)** | Contains the concealment × orientation matrix as an explicit 5-column × 6-row decision table (confirmed direct read); each cell specifies the register rule and what is held vs. deployable; [Case State], [Source Basis], and [Restoration Trace] block schemas; `claim_level` is surfaced when higher-order burdens are live so they are not collapsed into first-order content |
| pattern-profiling.md | **L (✓)** | Canonical owner for `claim_level` and `pattern_profile`; keeps PF-1 through PF-12 as a higher-order routing layer, makes claim-level conditional in routine first-order cases, and routes imported perfection/non-eventfulness through existing diagnostic owners rather than adding a PF code |
| noetic-reading-checklist.md | **L (✓)** | Shared NS definition; thin-basis / excerpt discipline; pattern-profile hand-off; explicit higher-order burden -> restoration-target hand-off present. |
| anti-patterns.md | **L (✓)** | 12 named anti-patterns: the original seven plus Excerpt Over-Read, Register-Hold Bypass, Restoration-First Default, Higher-Order Vocabulary Theater, and Semantic Gate Bypass. |
| mixed-case-handling.md | **L (✓)** | Compound case playbooks directly re-read in this pass, including (v) inherited-tradition/pre-inquiry and (vi) doctrinal-complexity; includes the non-Christian downstream-owner boundary, Variant A operator cue, and same-layer restoration-target typing rule. |
| hadith-authentication-epistemology.md | **L (✓)** | Compact canonical owner for corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed hadith-authentication cases; prohibits RT-5 inflation; gates downstream doctrinal release until the transmission burden is typed. |
| arabic-backbone-predicates.md | **L (✓)** | C-1/2/3 (criterion), T-1/2/3 (tribunal), O-1/2/3 (ordering), K-1/2 (category); NS-6 split rows for epistemological vs. ontological burden added Session 1 |
| seven-deformations.md | **L (✓)** | Routing summary table; 7 deformations + mushābara fāsida sub-type |
| discourse-orientation.md | **L (~)** | Four orientations: truth-seek, identity-perf, autotelic, zann-mode; not directly read |
| reason-disambiguation.md | **L (~)** | Four reason-categories (sound/corrupted/pseudo-neutral/inherited); not directly read |
| foreign-premise-detection.md | **L (✓)** | Detection steps; tribunal types; functional role classification; directly re-read in Session 8 |
| modes-of-concealment.md | **L (~)** | Seven concealment modes; not directly read but IR-schema integration confirmed |
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
| framework-pipeline.md | **L (✓)** | Session 5 adds prophetic-discourse-neutralization as a mandatory pass and blocks doctrinal dispatch while semantic-discipline work remains live |
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

| Code | Name | Rating |
|------|------|--------|
| V1 | Diagnostic (initial read) | **L (~)** |
| V2 | Reconstituting Reason | **L (~)** |
| V3 | Regress Dissolution | **L (~)** |
| V4 | Contamination Identification | **L (~)** |
| V5 | Directing Attention to Signs | **L (~)** |
| V6 | Convergence | **L (~)** |
| V7 | Taqlīd Check | **L (~)** |
| V8 | Bilā Kayf Anchor | **L (~)** |
| V9 | Necessary-Knowledge Priority | **L (~)** |
| V10 | Transmission/Content Vetting | **L (~)** |
| V11 | Taqlīd Transition | **L (~)** |
| V12 | Tamannaʿ Exhaustion | **L (~)** |

### Tactics

| Series | Files | Rating | Notes |
|--------|-------|--------|-------|
| E-series | E1–E4 (broadening-evidence, inferential-criterion, cumulative-case, cross-cultural-check) | **L (~)** | Individual files present |
| M-series | M1–M9 (self-refutation, prior-probability, orphaned-intuition, grief-register, deformation-triage, excluded-middle, definition-anchor, reductio, predication-mode) | **L (~)** | Individual files present; M1P (performative self-refutation) as sub-variant |
| R-series | R1–R3 (internalist-criterion, the-reminder, warranted-basic-belief) | **L (~)** | Individual files present |
| F-series | F1–F3 (supra-vs-antirational, volitional-dimensions, practice-epistemic-access) | **L (~)** | Individual files present |
| Auxiliary tactics | doubt-vs-skepticism.md, husn-al-nazar-arguments.md, inductive-fitri-method.md, symmetric-taqlid-check.md | **L (~)** | Individual files present; not directly read |

**Note on technique verification:** V-series, E-series, M-series, R-series, and F-series files all confirmed to exist in the file system. Individual file content not directly read in this pass. The (~) flag means: confirmed-present-by-directory-listing, not confirmed-content-by-read. A future audit pass should read each technique file against its usage claims in the case files and the IR schema.

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
| Islamic-specific moral objections (fiqh ethics, penal law, gender jurisprudence) | **P** | Covered by Type D usurpation routing (philosophical-usurpation.md) and NS-8 profile, but no dedicated DO treatment with objection/strongest-rebuttal/operative-response structure exists. Identification of usurpation is L; substantive response depth is P |
| Final-prophethood challenges — transmission layer | **L (✓)** | RT-1 through RT-4 in revelation-transmission.md |
| Final-prophethood challenges — moral-luck layer | **L (~)** | DO-8 (Prophetic Mission and Moral Luck) in do-second-loop.md |
| Final-prophethood challenges — prophetic authority vs. philosophy | **L (✓)** | prophecy-wahy-supremacy.md (challenge patterns A/B/C) |
| Comparative religion — Christianity | **L (✓)** | DO-11/DO-12/DO-13/DO-14 in do-christian-extensions.md; philosophical-usurpation.md Type A/B. DO-14 (added Session 3) governs Christian canon-selection confusion (which Bible version; Protestant/Catholic/Orthodox canonical diversity; authority-of-scripture-within-Christianity); case-profile block; three sub-question discrimination; criterion-gap opening to DO-10 |
| Comparative religion — cross-tradition via family transfer | **C** | Cases from any tradition that instantiate a governed family are covered through that family. Specific transfer routes: divine-multiplicity configurations (polytheism, henotheism, Hindu monistic/pluralistic-deity arrangements, apatheism) → V12 (tamannaʿ exhaustion; SKILL.md explicitly marks this as "any interlocutor" before DO-11/13 Christian overlay) + Creator-creation distinction in metaphysical-architecture.md; devotional-disorder (desire-as-worship, idolatry as fiṭrah-substitution) → hawā + ʿāda deformation types + F2 (volitional dimensions); cross-tradition philosophical-framework usurpation (Advaita non-dualism, Buddhist impermanence framework, Confucian naturalism as arbiter) → philosophical-usurpation.md Types A–D; religious-diversity objection → DO-4; noetic-structure diagnosis → NS-1 through NS-12 (no religious-background restriction). These transfer routes are operative architecture, not generic fallback. |
| Comparative religion — bespoke religion-specific families (Buddhist anatta / impermanence challenge to Islamic soul-doctrine; Hindu non-dualist Advaita as rival theological ontology; Jewish final-prophethood argument) | **M** | No dedicated DO-series case files. Cases whose argument structure requires religion-specific doctrinal content (not merely family-transfer engagement) have no canonical owner. Adherents of these traditions whose cases instantiate a governed family are engaged through that family — this entry captures only the bespoke argument-structure gap. |
| Conversation excerpt handling — thin-basis discipline | **C** | Governed across `noetic-reading-checklist.md` §Thin-Basis / Excerpt Mode, `mixed-case-handling.md`, P7 Stop-4, and `anti-patterns.md` §Excerpt Over-Read. |
| Hadith corpus transmission and authentication epistemology | **L** | `hadith-authentication-epistemology.md` now governs corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed downstream misuse; V10 remains the shared provenance -> contents -> authority technique; RT-1 through RT-4 remain Qurʾānic/scriptural rather than hadith codes |
| Sufism-related crises (contested practices, ṭarīqah authority claims) | **M** | Not governed; not referenced in SKILL.md activation scope but may arise in Muslim-internal cases |

---

## §10 — Gap Inventory (Partial and Missing Families)

The following are the actionable gaps in priority order based on scope-claim vs. governed-coverage distance:

### Resolved Check 1 — Conversation Excerpt Thin-Basis Discipline
**Claimed:** SKILL.md activation trigger includes "conversation excerpts."
**Governed:** `noetic-reading-checklist.md` now has a Thin-Basis / Excerpt Mode section, paired with `mixed-case-handling.md`, P7 Stop-4, and `anti-patterns.md` §Excerpt Over-Read. The committed repo supports the C rating.
**Residual risk:** Low. The remaining risk is operator discipline on thin excerpts, not owner absence or release-state mismatch.
**Regression check:** Keep the checklist, Stop-4, anti-pattern, and ledger status aligned whenever excerpt discipline changes.

### Resolved Check 2 — Register-Hold Bypass Failure Detection
**Claimed:** The concealment × orientation matrix in case-state-schema.md governs content deployability at Gate Check 6.
**Governed:** The matrix is explicit and the named anti-pattern exists in anti-patterns.md. The failure signature and the governing matrix now point to each other cleanly.
**Residual risk:** Low — the remaining risk is operator discipline, not owner ambiguity.
**Regression check:** Keep the matrix cell and anti-pattern aligned whenever either file changes.

### Gap 3 — Do-Core and Do-Second-Loop Failure Tests (unverified)
**Claimed:** DO-1 through DO-10 are L.
**Governed:** DO-1 and DO-2 confirmed to have the objection/rebuttal/operative-response structure. DO-3 through DO-10 were directly read in Session 5 for terminology cleanup and routing review; content depth is present, but explicit failure-test blocks still remain thinner than ideal.
**Risk:** If DO-3 through DO-10 lack explicit failure tests or self-audit questions, they are structurally P rather than L.
**Remediation:** Direct read of do-second-loop.md and do-core.md DO-3 through DO-6 entries; add failure-test blocks where absent.

### Gap 4 — Islamic-Specific Moral Objections (P → C or L)
**Claimed:** NS-8 profile covers moral-recoil component; Type D philosophical usurpation covers liberal-political-philosophy-as-moral-arbiter.
**Governed:** Usurpation identification is L; substantive response structure for specific Islamic ethics objections is absent.
**Risk:** A practitioner correctly identifies Type D usurpation and routes to NS-8 but lacks a structured response to the specific content of the objection (e.g., corporal punishment, slavery in Islamic law, gender asymmetry in testimony or inheritance).
**Remediation:** Note: DO-14 was used for "Christian Canon Selection Confusion" (Session 3), not for "Islamic Ethics Objections." The code for a future Islamic-ethics case file would be DO-15 or an NS-8 extension.

### Gap 5 — Comparative Religion: Bespoke Religion-Specific Families (M, correctly bounded)
**What is governed:** The repo governs comparative-religion cases at two levels that must not be conflated. (1) Explicit Christian extensions: DO-11/DO-12/DO-13 in do-christian-extensions.md. (2) Cross-tradition family-transfer coverage: any case from any tradition that instantiates a governed family is covered through that family — specifically: divine-multiplicity (polytheism, henotheism, Hindu monistic/pluralistic-deity, apatheism) via V12 + Creator-creation distinction; devotional-disorder (desire-as-worship, idolatry) via hawā/ʿāda deformation + F2; cross-tradition philosophical-framework usurpation via philosophical-usurpation.md Types A–D; religious-diversity via DO-4; noetic-structure diagnosis via NS-1 through NS-12. These are operative architecture, not generic fallback.
**What is not governed:** Bespoke argument structures that require religion-specific doctrinal content and cannot be resolved through family transfer: (a) Buddhist anatta/no-soul as a direct challenge to the Islamic account of the nafs; (b) Hindu non-dualist (Advaita Vedanta) claim as a rival theological ontology; (c) Jewish final-prophethood arguments grounded in Torah's self-characterization as complete; (d) Buddhist impermanence framework as a rival account of creation and divine constancy. These remain M.
**Risk:** Conflating the two levels — treating "no bespoke file exists" as "no coverage exists" — causes the practitioner to misrepresent the repo's reach and may suppress correct routing through family transfer for a Hindu or Buddhist interlocutor whose case actually does instantiate a governed family.
**Remediation:** SKILL.md and coverage-ledger corrected to distinguish both levels. Bespoke-family gap remains; remediation requires dedicated case content, not a description fix.

### Resolved Check 6 — Hadith Transmission and Authentication Epistemology
**Claimed:** "transmission and final-prophethood challenges" in SKILL.md.
**Governed:** `hadith-authentication-epistemology.md` now provides a compact canonical owner for corpus skepticism, method skepticism, report-class / epistemic-yield questions, grade confusion, and mixed doctrinal misuse; V10 remains the shared provenance -> contents -> authority technique; `revelation-transmission.md` stays scoped to RT-1 through RT-4 instead of carrying hadith as an interim overlay.
**Residual risk:** Low. The remaining non-goal is a full hadith-science encyclopedia. This repo now governs the routing and release discipline the gap required without attempting a full specialist manual.

### Gap 7 — Mode-of-Concealment File (unverified)
**Claimed:** Modes of concealment are L based on cross-reference.
**Verified:** modes-of-concealment.md exists; content not directly read.
**Risk:** Low — the IR schema fields and routing-precedence references make it structurally implausible that this file is absent — but the content has not been directly audited for failure conditions or self-audit questions.
**Remediation:** Add to next direct-read pass.

---

## §11 — Audit Confidence Summary

These counts now describe the live workspace baseline through Session 12.

| Confidence level | Count | Notes |
|-----------------|-------|-------|
| **L (✓)** — directly read and confirmed | 52 entries | All entries where the canonical file was read in Session 1, Session 2, or the new Session 11 hadith owner pass |
| **L (~)** — confirmed by cross-reference | 47 entries | File confirmed to exist; content confirmed by dependent-file references; not directly read |
| **P** — partial (identified gap) | 2 entries | do-core DO-3–DO-6 failure tests (unverified), Islamic moral objections |
| **M** — missing/implied | 2 entries | bespoke religion-specific comparative families, Sufism-related crises |

**Total governed families/files:** ~107 entries across NS, DO, RT, deformations, concealment, governance procedures, techniques, semantic gates, pattern profiling, and special domains.

**Claimed but not fully governed (current workspace baseline):** partials remain do-core / do-second-loop failure-test depth and Islamic moral objections depth. Missing or bounded gaps remain bespoke religion-specific comparative families and Sufism-related crises. `modes-of-concealment.md` remains an L-by-cross-reference file that still needs a direct-read verification pass; it is not a missing family.

---

## §13 — Canonical Owner Map

This map distinguishes three functional roles files play in the architecture. Each file has exactly one primary role; some files serve secondary roles where noted.

| Role | Definition | Files |
|------|------------|-------|
| **Routing** | The file's primary job is to direct the practitioner to the correct next file, module, or instrument. It does not supply response content. | `case-library/INDEX.md`, `case-library/profiles/INDEX.md`, `references/diagnostics/INDEX.md`, `references/tactics/INDEX.md`, `references/techniques/INDEX.md`, `references/procedures/INDEX.md`, `references/diagnostics/framework-pipeline.md`, `references/diagnostics/routing-precedence.md`, `case-library/noetic-profiles.md` (redirect-only) |
| **Diagnostic** | The file's primary job is to classify the case — the noetic state, deformation type, concealment mode, discourse orientation, claim-level, pattern-profile, reason-category, foreign-premise status, or semantic blocker family. It produces typed state that feeds the IR. | `V1-diagnostic.md`, `noetic-reading-checklist.md`, `seven-deformations.md`, `modes-of-concealment.md`, `discourse-orientation.md`, `reason-disambiguation.md`, `pattern-profiling.md`, `foreign-premise-detection.md`, `arabic-backbone-predicates.md`, `diagnostic-ir.md`, `case-state-schema.md`, `mixed-case-handling.md`, `kalamic-interlocutor.md`, `fitrah-perspectives.md`, `hadith-authentication-epistemology.md`, `prophetic-discourse-neutralization.md`, `causal-series-taxonomy.md`, `definition-discipline.md`, `proof-method-audit.md`, `perfection-criterion-usurpation.md` |
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
| 2026-04 Session 3 | Pattern-family robustness + multi-module routing discipline audit + profile-patterning patch set | pattern-family-audit.md: 8-deliverable audit document created (pattern-family map PF-1 through PF-12; coverage/ownership audit; routing/cumulative-dispatch audit; abstraction-level audit; ranked gap list GAP-A through GAP-I; file-by-file patch plan; regression fixture suite F1–F8; production-readiness judgment). Patches implemented: (A) do-christian-extensions.md — DO-14 added (Christian Canon Selection Confusion; case-profile block; three sub-question discrimination; criterion-gap opening; prohibited moves; NS pairing); (B) mixed-case-handling.md §(vi) — Doctrinal Complexity three-profile playbook added (vi-A inquiry, vi-B deflection/iʿrāḍ, vi-C criterion-pressure; case-profile blocks; minimal-pair discriminators); (C) mixed-case-handling.md §(v) — Inherited Christian Framework + Pre-Inquiry compound playbook added (case-profile routing rule, not surface-pattern trigger; regression-repair for restoration-first, Christology-preemption, RT-2 collapse, criterion-grant failure modes; FPD gate; sub-question discrimination; pass/fail checks for four named failures); (D) V12-tamanuc-exhaustion.md — cross-tradition scope statement added (structural trigger, not tradition-specific; Advaita gap noted); DO-11→DO-12 stopping conditions added (sequential only; P-3 violation named; authority-shift → V10+RT-2 redirect); (E) do-second-loop.md — Comparative-Prophethood Opening-Frame Dispatch section added (DO-10 → DO-4 → prophecy-wahy-supremacy.md sequence with structural dependency; stopping conditions across levels; case-profile block); (F) philosophical-usurpation.md — cross-tradition scope added to frontmatter (types keyed to framework, not interlocutor background; illustrative examples per type); (G) revelation-transmission.md — Interim Hadith-Transmission Routing section added (three case-profile forms: isnād skepticism, āḥād epistemology, historical-critical import; instruments that apply; explicit architecture-end statement); V1-diagnostic.md — specialty-marker list updated (DO-14 added; hadith interim routing noted; exhaustive-vs-illustrative clarification added); coverage-ledger §2 DO-14 row added; §9 comparative-religion row updated; Gap 4 remediation note (DO-14 used for Christian canon, not Islamic ethics; next code = DO-15); Gap 6 upgraded from M to partial C; this revision log row added |
| 2026-04 Session 4 | Generalize-upward pass — tests, distinctions, and routing logic lifted to highest valid structural level | Four patches implemented: (H1) V10-transmission-content-vetting.md — `> scope:` cross-tradition statement added to frontmatter; "Recognition vs. creation principle (cross-traditional)" named and placed in Step 3; "Canon-authority structural form (cross-traditional)" block added in Step 3 with criterion-circularity structure named across Protestant/Catholic/Jewish/Hindu traditions; Branch B "Route after" updated to include DO-14 for Christian authorization cases. V10 is now the generalized structural owner of the canon-authority-criterion level; tradition-specific branch operators remain. (H2) mixed-case-handling.md §(v) — title generalized from "Christian-Background Pre-Inquiry" to "Inherited-Tradition Background — Pre-Inquiry Compound"; activation condition (1) generalized from "Christian tradition, any denomination" to "any tradition — Christian, Jewish, secular-progressive, Hindu, or other"; feature (3) generalized from Christian-specific module list to structural description; tradition-specific routing note added (Christian dispatch = DO-14 → DO-10; Jewish/Hindu = V10 Step 3 structural form + no dedicated DO module yet; secular = Type B usurpation). (H3) do-christian-extensions.md DO-14 sub-question (c) — structural pointer added: "the criterion-circularity form of this sub-question is cross-traditional; V10 Step 3 §(Canon-authority structural form) is the generalized structural owner; DO-14 is its Christian instantiation." (H4) coverage-ledger.md — §3 V10 routing note extended; §9 compound/mixed cases row updated to reflect §(v) generalization; this revision log row added. What remained tradition-specific: DO-14's three sub-question structure and the specific Protestant/Catholic/Orthodox corpora, formation events, and authorization arguments; §(v)'s Christian-specific dispatch table (DO-14 → DO-10 → DO-11/12); V10 Branch A (Qurʾān-specific transmission conditions); V10 Branch B (Biblical manuscript conditions); V10 Branch C (Hadith isnād conditions). No fake universals created: Jewish/Hindu authority-certification cases are routed to V10 Step 3 structural form with explicit "no dedicated DO module yet" notation. |
| 2026-04 Session 5 | Volume 1–4 semantic-gate and owner-hardening pass | New canonical diagnostic owners landed: prophetic-discourse-neutralization.md (semantic recontenting vs. evacuation), causal-series-taxonomy.md, definition-discipline.md, proof-method-audit.md, perfection-criterion-usurpation.md. Shared governance hardened: diagnostic-ir.md and case-state-schema.md now carry upstream findings plus `semantic-discipline-required`; framework-pipeline.md adds prophetic-discourse-neutralization before content release; routing-precedence.md and mixed-case-handling.md preserve ordered sequencing for tribunal + semantic blocker compounds; foreign-premise-detection.md now distinguishes criterion import, tribunal installation, and transmission demotion. Semantic routing hardened: M9-predication-mode.md now canonically owns loaded negative theological terms; V8 hard-routes such terms through M9 first; do-attribute-precision.md and kalamic-interlocutor.md updated to require semantic disaggregation before doctrinal release. Branding cleanup performed in do-core.md, do-second-loop.md, do-christian-extensions.md, sound-reason-epistemology.md, terminology.md, fitrah-perspectives.md, ns-8-muslim-internal-crisis.md, case-library/INDEX.md, and this ledger. |
| 2026-04 Session 6 | Integrative grokking pass | New operational owner landed: pattern-profiling.md, separating live `claim_level` / `pattern_profile` emission from the historical pattern-family audit. Core governance aligned: case-state-schema.md, diagnostic-ir.md, diagnostic-ir.schema.json, framework-pipeline.md, routing-precedence.md, mixed-case-handling.md, noetic-reading-checklist.md, module-codes.md, SKILL.md, and README.md now surface higher-order burdens explicitly and route them before first-order case content. Ledger drift corrected: Register-Hold Bypass contradiction removed; anti-pattern count updated; case-library/INDEX.md now includes DO-14 in live routing. Terminology normalized around upstream-tribunal language and the secondary restorative route. |
| 2026-04 Session 7 | Corrective verification pass | Restored live mixed-case playbooks (v) inherited-tradition/pre-inquiry compound and (vi) doctrinal-complexity routing; relaxed `claim_level` from always-required surfaced output to conditional higher-order emission while preserving IR gating; fixed stale DO-14 and P-D routing references; added owner-local guards for perfection-criterion, causal-impossibility, loaded-term, source-native-foundation, and hadith/transmission boundary drift; marked production-hardening-audit.md as a local workspace-only historical non-governing audit substrate. |
| 2026-04 Session 8 | Narrow parity / truthfulness / governance-surface hardening pass | Re-verified that `case-state-schema.md`, `diagnostic-ir.md`, and `diagnostic-ir.schema.json` already carry live `claim_level` / `pattern_profile` fields on-wire, so Path 1 remains live without further wire expansion; tightened `mixed-case-handling.md` §(v) so non-Christian inherited-tradition compounds stop honestly at V10 Step 3 when no dedicated downstream owner exists and do not borrow DO-14 by analogy; tightened §(vi) Variant A with a bounded operator cue for the smallest structural answer; reconciled ledger recency metadata; upgraded `framework-pipeline.md`, `mixed-case-handling.md`, and `foreign-premise-detection.md` to direct-read confirmation; re-read `README.md` and left it untouched at that pass stage because its higher-order / IR claims remained materially aligned to the repo. |
| 2026-04 Session 9 | Readiness / grokking hardening pass | README operational-governance prose, architecture table, and repository mermaid were tightened to tell the State 1 story explicitly; `noetic-reading-checklist.md` gained a higher-order hand-off section; `mixed-case-handling.md` gained same-layer restoration-target typing language; `anti-patterns.md` gained Higher-Order Vocabulary Theater; `heuristics.md` rule 29 now distinguishes burden / pattern / target; `framework-pipeline.md` now names conditional higher-order emission and audit companions; stale excerpt-gap prose in this ledger was retired. |
| 2026-04 Session 10 | Commit-parity hardening pass | Reconciled the previous self-report against committed GitHub `main`; confirmed that the stronger noetic hand-off, higher-order anti-pattern, heuristics non-collapse rule, framework-pipeline audit-companion notes, and README architecture surfaces are all committed; removed stale "local-only / uncommitted" Session 8 / Session 9 narration from this ledger; and closed the remaining excerpt-discipline release-state mismatch so the ledger now describes committed reality. |
| 2026-04 Session 11 | Hadith-transmission and authentication hardening pass | Added `hadith-authentication-epistemology.md` as the compact canonical owner for hadith corpus/authentication routing; updated SKILL.md, diagnostics/INDEX.md, case-library/INDEX.md, revelation-transmission.md, V10, module-codes.md, diagnostic-ir.md, routing-precedence.md, pattern-profiling.md, and module-catalogue.json so hadith pressure no longer blurs into RT-1 through RT-4 and no RT-5 is invented; upgraded the hadith-authentication coverage row from M to L and retired Gap 6 as a resolved check. |
| 2026-04 Session 12 | v0.1.0.0 release truthfulness / packaging pass | Added a bounded initial-release scope note to README.md so the GitHub landing page does not overclaim toward `1.0`; updated this ledger's recency metadata to describe the release-packaged workspace baseline without changing the substantive gap inventory or pretending the remaining bounded gaps were closed. |
| 2026-04 Session 13 | Concealment-hardening and output-layer separation pass | Normalized concealment typing across SKILL.md, modes-of-concealment.md, noetic-reading-checklist.md, case-state-schema.md, diagnostic-ir.md, diagnostic-ir.schema.json, routing-precedence.md, and module-codes.md so the axis emits `clear` when resolved absent and `mode-?` when unresolved rather than blanks or `none confirmed`; clarified that register-hold governs Layer B direct deployment without erasing Layer A complete diagnostic output; hardened P6 for worldview-deflection / pseudo-neutrality slogans; and added the exact "I have no religion, I just follow the evidence wherever it leads" regression fixture to pattern-family-audit.md. |
| 2026-04 Session 14 | Selective-routing hardening and release-packaging fidelity pass | Tightened the enforcement layer around current-pass activation, hold/stop-operativity, and boundary reset without collapsing Layer A diagnostic intelligibility or warranted layered composition: SKILL.md, case-state-schema.md, diagnostic-ir.md, diagnostic-ir.schema.json, routing-precedence.md, framework-pipeline.md, heuristics.md, anti-patterns.md, and pattern-family-audit.md now distinguish active coordination from diagnosed-but-held routes and keep stop/hold states operative in IR/output governance. README.md release scope and packaging guidance were also corrected for `v0.1.0.2`, replacing Windows zip instructions with Bash / WSL / Linux archive generation so published skill bundles keep slash-safe entry paths. |
