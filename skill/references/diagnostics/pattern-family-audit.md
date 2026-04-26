---
id: pattern-family-audit
module_class: governance
canonical_path: skill/references/diagnostics/pattern-family-audit.md
contract_version: "0.2.2.0"
load_when:
  - auditing pattern-family coverage, routing discipline, or running regression tests
catalogue_registered: false
---

# Pattern-Family Robustness and Multi-Module Routing Discipline Audit

---

## §1 — Pattern-Family Map

Each family below is derived from the repo's file structure and read against the anchor case. The map is abstract-first: pattern definition precedes surface realizations. `pattern-profiling.md` is now the operational owner for live `claim_level` and `pattern_profile` emission; this file remains the long-form audit and regression reference.

State note: the sections below preserve the audit-time snapshot so the regression history stays inspectable. When a snapshot statement conflicts with the live repo, the current owner files, `pattern-profiling.md`, and the revision log govern.

---

### PF-1 — Inherited Framework / Habituated Belief

**Abstract pattern:** The interlocutor holds beliefs from upbringing, community, or cultural absorption rather than from examined conviction. The inherited framework functions as an unreconstituted filter: new information is evaluated through it rather than examined alongside it.

**Surface realizations:** "I was raised as X", "my family has always been Y", implicit framework comparison ("I was Christian / grew up secular"), background assumptions about what counts as evidence.

**Noetic pressures:** iʿtiqādāt mawrūtha operating at the level of basic commitments; the framework is pre-reflective and therefore invisible to the interlocutor. The interlocutor frequently presents evidential demands that are actually expressions of the unreconstituted filter.

**Concealment / deformation dynamics:** Primary deformation = iʿtiqādāt mawrūtha; secondary = ʿāda (if the framework has been habituated over many years); concealment typically iʿrāḍ (the question has not been allowed to press against the framework).

**Canonical routing surfaces:** `seven-deformations.md` (iʿtiqādāt mawrūtha section) + `mixed-case-handling.md §(iv)`

**Primary module cluster:** V2 (reconstitute the conception of reason), V7 (symmetric taqlīd check), V11 (taqlīd-transition)

**Secondary modules:** P1 (fiṭrah restoration), R3 (warranted basic belief), E2 (inferential criterion)

**Co-dispatch conditions:** V2 must land before any evidential content (E1/E3). V7 can co-dispatch with V2 once initial triage confirms the criterion is the live issue. P1 can co-dispatch in positive-register cases where no hostile criterion is operating.

---

### PF-2 — Evidentialist Demand / Pre-Inquiry ("No Reason")

**Abstract pattern:** The interlocutor requests justification but has not yet formed a genuine inquiry. The "no reason" claim is a pre-inquiry position, not an examined conclusion. Frequently, an implicit criterion functions as the tribunal; the demand to "give me a reason" means "give me a reason that passes this specific bar."

**Surface realizations:** "I don't have any reason to be Muslim", "give me evidence", "what's the proof?", "it needs to pass scientific scrutiny."

**Noetic pressures:** NS-2 (agnostic evidentialist) or NS-12 (blank slate). The phrasing is ambiguous between (a) genuine truth-seeking inquiry and (b) criterion-enforcement demanding religion pass a foreign bar. The discourse orientation (truth-seek vs. autotelic vs. zann-mode) is the key differentiator.

**Concealment / deformation dynamics:** ẓann (holding the demand as examined when it isn't); iʿtiqādāt mawrūtha (if a specific criterion is functioning as tribunal); iʿrāḍ as concealment if the demand is pre-inquiry rather than formed inquiry.

**Canonical routing surfaces:** `foreign-premise-detection.md` (detect first), `V2` (if criterion detected), `E2` (inferential criterion — if truth-seek orientation confirmed with no hostile criterion)

**Primary module cluster:** `foreign-premise-detection.md`, then V2 (if criterion detected), or E2 / E1 (if clear truth-seek with no upstream criterion)

**Secondary modules:** M2 (prior probability — surface the prior when it's set so low evidence cannot land), E3 (cumulative-case — only when no single upstream blocker and register is open)

**Co-dispatch conditions:** FPD output governs everything else. V2 must precede all evidential content if a criterion is detected. If FPD = none-detected and DO-orient = truth-seek: E2 → E1 → E3 in order, with stopping conditions active.

---

### PF-3 — Canon Formation / Text Selection / Authority Certification

**Abstract pattern:** The interlocutor challenges which version of a text is authoritative, which community has the right account, or who decided the canon. The challenge can be directed at the interlocutor's own background tradition (Christian Bible selection) or at Islam's scriptures.

**Two versions:**
- **PF-3A — Christian canon selection** (which Bible version — Protestant / Catholic / Orthodox): The live question is about a tradition the interlocutor comes from; the challenge is identifying why any version is authoritative. **Currently ungoverned as a named family** — gap GAP-A.
- **PF-3B — Islamic canon formation** (why these surahs, the ʿUthmānic compilation, whether community-selection undermines authority): Governed by `revelation-transmission.md RT-2`.

**Surface realizations:** "Which Bible version — Protestant or Catholic?", "who decided which books to include?", "why is there disagreement about the canon?", "I heard the Qurʾān was compiled later."

**Noetic pressures:** NS-9 (historical-critical skeptic) when skepticism is methodologically formed; NS-7 (theistic evidentialist) when the interlocutor is Christian and seeking authority grounds; often thin-basis cases requiring underdetermined routing.

**Concealment / deformation dynamics:** ẓann (complexity treated as refutation); iʿtiqādāt mawrūtha (historical-critical assumptions imported); concealment often iʿrāḍ (canon complexity used as an exit, not genuine inquiry).

**Canonical routing surfaces (PF-3B):** `revelation-transmission.md RT-2`, `V10` (separate artifact from transmission), `ns-9` profile if skepticism is methodologically formed

**Canonical routing surfaces (PF-3A):** MISSING — see GAP-A. After Patch A, routes to `do-christian-extensions.md DO-14`.

**Co-dispatch conditions:** PF-3B → V10 before any RT-2 content; if NS-9 confirmed → V2 first on historical-critical framework. PF-3A → after Patch A, the DO-14 entry specifies the internal sequencing.

---

### PF-4 — Transmission / Preservation / Authentication

**Abstract pattern:** Challenge to the reliability of transmission — whether a text has reached us accurately, whether it was corrupted, or whether the chain of transmission is trustworthy. Structurally distinct from PF-3 (canon formation / authority): this family is about reliability of transmission, not legitimacy of inclusion.

**Surface realizations:** Manuscript fragment claims ("we found an earlier version"), qirāʾāt confusion ("different Qurʾāns"), "the Bible was changed," claims that preservation was inconsistent.

**Noetic pressures:** NS-9 (historical-critical skeptic) when scholarly framework is explicit; NS-3 (deconverted) when text-historical concerns contributed to a prior exit from a tradition.

**Concealment / deformation dynamics:** iʿtiqādāt mawrūtha (historical-critical framework imported as neutral method); shubhah (legitimate intellectual content remains once the framework is loosened); discourse orientation often truth-seek with genuine scholarly interlocutors.

**Canonical routing surfaces:** `ns-9-historical-critical-skeptic.md` profile, `V10` (provenance → contents → authority), `revelation-transmission.md RT-1/RT-3`

**Primary module cluster:** V2 (loosen historical-critical framework), V10, RT-1 (artifact vs. authenticated transmission), RT-3 (qirāʾāt vs. manuscript variants)

**Secondary modules:** K-1 check (arabic-backbone-predicates.md — category error check), P2 (objection mapping to prevent conflation of RT-1/RT-2/RT-3)

**Co-dispatch conditions:** V2 before any RT case if NS-9 confirmed; V10 before any RT content; K-1 check alongside V2 when category conflation (qirāʾāt-as-variants) is visible.

---

### PF-5 — Doctrinal Complexity / "Why Is This So Complicated?"

**Abstract pattern:** The presence of scholarly disagreement, internal diversity, or complex doctrinal detail is experienced as evidence against the tradition's reliability, or as a reason not to engage. This family has three distinct variants that require different routing.

**Three variants:**
- **PF-5i — Genuine inquiry**: "I find this complicated and want to understand." P4 (maieutic) applies; complexity is an invitation, not an objection.
- **PF-5ii — Iʿrāḍ / deflection**: Complexity is used as an exit ("too many opinions, I can't engage"). Concealment mode = iʿrāḍ; relational-only register; no content.
- **PF-5iii — Criterion-pressure**: Disagreement-implies-falsehood, treated as a logical argument. FPD: foreign criterion ("agreement is the test of truth"). V2 on the criterion before any content about scholarly diversity.

**Surface realizations:** "Why is Islam so complicated?", "there are too many different opinions", "scholars can't agree on basic things so nobody really knows", "this is overwhelming."

**Noetic pressures:** NS-12 (blank slate) if genuinely uncertain; NS-3 (deconverted) if complexity weaponized from prior religious disappointment; NS-7 if the interlocutor seeks certainty-through-demonstration.

**Concealment / deformation dynamics:** ʿāda (intellectual avoidance habituated); ẓann (complexity treated as resolved against); iʿrāḍ as concealment when complexity is used to not engage.

**Canonical routing surfaces:** MISSING as a named family — GAP-B. After Patch B, routes through mixed-case-handling.md §6 which owns the three-variant decision tree.

**Primary module cluster (pending Patch B):** discourse-orientation.md (establish DO-orient before content), then P4 (for PF-5i), or relational-only (for PF-5ii), or V2 + FPD (for PF-5iii).

**Co-dispatch conditions:** Discourse orientation must be established before any content is loaded. If iʿrāḍ confirmed → hold all content. If criterion-pressure confirmed → V2 first. If genuine inquiry → P4 / P3.

---

### PF-6 — Christology / Trinity / Jesus-Status

**Abstract pattern:** Specific claims about Jesus, the Trinity, the Incarnation, or the philosophical coherence of Trinitarian theology. Often arises from Christian background, constituting both an objection to Christianity and a potential criterion for evaluating Islam. In anchor-case contexts, the interlocutor's own uncertainty about the Trinity may be the presenting frame.

**Surface realizations:** "How can God be three?", "is Jesus God?", "the Trinity doesn't make sense", "why do Christians believe in the Incarnation?", "if God is one, how can Jesus be divine?"

**Noetic pressures:** NS-7 (theistic evidentialist seeking philosophical coherence); NS-3 (deconverted — Christian crisis may have already occurred); NS-11 (fideist — holding Trinity on faith, resistant to rational examination).

**Concealment / deformation dynamics:** iʿtiqādāt mawrūtha (Trinity as inherited commitment); shubhah (specific logical puzzles about the doctrine — genuine intellectual content once framework loosens); concealment varies by profile (truth-seek if genuinely puzzled; identity-performance if Christian framework is identity-constituting).

**Canonical routing surfaces:** `V12` (base logical exhaustion — always first), `do-christian-extensions.md` (DO-11 / DO-12 / DO-13 as Christian-specific overlay on V12)

**Primary module cluster:** V12 → DO-11 (perfect-being multipersonality pressure) → DO-12 (logical problem of three-in-one) sequentially

**Secondary modules:** V8 (bilā kayf anchor for attribute-language alongside any DO entry), M2 (prior probability — useful framing once V12 is in place)

**Co-dispatch conditions:** V12 MUST precede DO-11/DO-12 — they presuppose it, not substitute for it. Check concealment × orientation matrix before loading any DO content: if identity-performance governs, hold doctrinal content entirely (Register-Hold Bypass anti-pattern applies). DO-11 stopping condition: hold DO-12 until DO-11 has visibly engaged the interlocutor; do not stack both without pause.

**Critical routing note:** When "Christian" appears in the interlocutor's description but no active Trinity challenge is present (anchor case pattern), V12 and DO-11 are NOT triggered. The interlocutor's background activates PF-1 (inherited framework) and PF-8 (positive restoration) — not PF-6.

---

### PF-7 — Comparative Prophethood / Why Islam and Not Another Religion?

**Abstract pattern:** The question of what distinguishes Islamic prophethood from other traditions' prophetic claims, or why this particular revelation should be accepted over alternatives. Often presents as religious-diversity pressure or as a sincere theistic inquiry from an already-believing interlocutor.

**Surface realizations:** "Why should I be Muslim and not Christian?", "multiple religions claim prophethood", "what makes Muhammad different?", "I respect him as a historical figure but don't see why he's the final prophet."

**Noetic pressures:** NS-2 (agnostic evidentialist — seeking comparative evidence); NS-7 (theistic evidentialist — already accepts God, pressing the specific prophetic claim); NS-12 (blank slate — genuinely open).

**Concealment / deformation dynamics:** ẓann (treating multiple claims as equal without examination); iʿtiqādāt mawrūtha (if a specific tradition's standard is imported as the criterion for evaluating prophethood); discourse orientation often genuine truth-seek when the question is sincere.

**Canonical routing surfaces:** `do-core.md` (DO-4 for religious diversity), `do-second-loop.md` (DO-10 for three-tiered epistemological structure), `prophecy-wahy-supremacy.md`

**Primary module cluster:** DO-10 (fiṭrah → khabar → naẓar ʿaqlī — the structural answer to "why this specific claim"), DO-4 (religious diversity — why multiple claims don't cancel each other), prophecy-wahy-supremacy.md (specific prophetic credentials)

**Secondary modules:** E4 (cross-cultural check), `do-christian-extensions.md` (if specifically comparing with Christian prophethood claims)

**Co-dispatch conditions:** DO-10 governs the structural architecture; DO-4 addresses the relativist challenge; specific prophetic credentials follow only after the epistemological structure is established. No explicit dispatch declaration exists in a single file — see GAP-E.

---

### PF-8 — Positive Restoration / Opening Framing

**Abstract pattern:** The interlocutor is in a pre-inquiry state — not presenting a structured objection but potentially open, and the primary work is restoration of fiṭrī capacity rather than rebuttal. The case has minimal deformation and maximal openness.

**Surface realizations:** "I'm not sure what I believe", "I was raised as X but don't know anymore", genuinely exploratory phrasing without formed objections, "I'm just curious about Islam."

**Noetic pressures:** NS-12 (blank slate — dual fiṭrah, both rational and volitional dispositions active); NS-3 (deconverted but unresolved — religious journey still in motion).

**Concealment / deformation dynamics:** Minimal deformation if genuinely open (best restoration candidates); possibly ʿāda if prior religious environment is still in play; concealment = iʿrāḍ only if complexity has become the exit.

**Canonical routing surfaces:** `P1-fitrah-restoration.md`, `P4-maieutic.md`, `ns-12-blank-slate-dual-fitrah.md`

**Primary module cluster:** P1 (fiṭrah restoration), P4 (maieutic — draw out dormant recognitions), V5 (directing attention to signs)

**Secondary modules:** R2 (the reminder), F3 (practice and epistemic access), M3 (orphaned intuition — if prior framework still active)

**Co-dispatch conditions:** This family MUST NOT have doctrinal rebuttal co-dispatched in the opening move. Restoration precedes argument. V12, DO-series, and RT-series entries are all held until the register shifts.

---

### PF-9 — Self-Refutation / Performative Incoherence

**Abstract pattern:** The interlocutor's framework or criterion is internally self-defeating; the criterion cannot pass its own test. The critical move is to surface this before any content engagement, as it may dissolve the objection entirely.

**Canonical routing:** M1, M1-P (always first when the criterion is self-refuting)

**Co-dispatch:** M1 before any content; if M1 lands cleanly, do not immediately add argument — allow the landing to work (P-3: no stacking after a landed move).

---

### PF-10 — Grief / Existential Pressure / Problem of Evil

**Abstract pattern:** Emotional or existential objection rooted in suffering or personal loss. The intellectual layer (DO-2 — problem of evil) is downstream and held until the relational register is established.

**Canonical routing:** M4 (grief register — governs); DO-2 held pending M4 establishing the register. `mixed-case-handling.md §(i)` specifies the sequencing playbook.

---

### PF-11 — Muslim-Internal Crisis / Authority Fatigue / Textual Destabilization

**Abstract pattern:** A Muslim believer experiencing internal pressure — authority wound, loss of confidence in scholars, textual shubuhāt, moral recoil from specific rulings. Distinct from external debate: the goal is examined conviction, not external rebuttal.

**Canonical routing:** NS-8 profile, RT-4 (pastoral register for textual destabilization), P5 (already-believing), `mixed-case-handling.md §(ii)`.

---

### PF-12 — Philosophical Naturalism / Scientific Materialism

**Abstract pattern:** Hard naturalist criterion operating as upstream filter — causal closure, empirical verifiability requirement, HADD/CSR debunking arguments. The criterion is the real issue; any content engagement without addressing it is filtered out.

**Canonical routing:** NS-1 → V2 (mandatory first) → FPD (Type B philosophical usurpation) → DO-7 (HADD/CSR) if specifically targeting theistic recognition. M1 if the criterion is self-refuting (empirical testability is not itself empirically testable).

---

## §2 — Coverage and Canonical-Ownership Audit

| Family | Canonical Owner | Ownership Clarity | Rating |
|--------|----------------|-------------------|--------|
| PF-1: Inherited Framework | `seven-deformations.md` (iʿtiqādāt mawrūtha) + `mixed-case-handling.md §(iv)` | Partial — assembled from deformation + technique files; no single named "inherited-framework family" declaration | P |
| PF-2: Evidentialist Demand | `foreign-premise-detection.md` + V2 (if criterion) | Partial — detection pass is owned; "pre-inquiry evidentialist demand" as a family pattern is incidental | P |
| PF-3A: Christian Canon Selection | **NONE** | Missing — GAP-A | M |
| PF-3B: Islamic Canon Formation | `revelation-transmission.md RT-2` | Good — RT-2 is well-scoped; scope boundary is explicit | L |
| PF-4: Transmission/Authentication | `revelation-transmission.md RT-1/RT-3` + `ns-9` | Good — RT-1/RT-3 are well-scoped; V10 governs sequencing | L |
| PF-5: Doctrinal Complexity | **NONE** | Missing — GAP-B | M |
| PF-6: Christology/Trinity | `V12` + `do-christian-extensions.md` | Good — V12 + DO-11/12/13 are well-scoped; sequencing explicit | L |
| PF-7: Comparative Prophethood | `do-second-loop.md DO-10` + `prophecy-wahy-supremacy.md` + DO-4 | Partial — no single file declares the canonical dispatch sequence | P |
| PF-8: Positive Restoration | `P1-fitrah-restoration.md` + `ns-12` | Partial — P1 is the dedicated procedure; "opening-frame with minimal deformation" isn't a named case family | P |
| PF-9: Self-Refutation | `M1`, `M1-P` | Good — well-defined and self-owned | L |
| PF-10: Grief/Existential | `M4` + `mixed-case-handling.md §(i)` | Good — M4 is clearly owned; sequencing explicit | L |
| PF-11: Muslim-Internal Crisis | `ns-8` + RT-4 + P5 | Partial — compound case in mixed-case-handling.md, not standalone family file | P |
| PF-12: Philosophical Naturalism | `ns-1` + `philosophical-usurpation.md Type B` | Good — NS-1 profile clear; Type B named | L |

**Rating legend:** L = Landed (canonical owner, typed routing, IR-visible); P = Partial (incidental support, assembled from other files); M = Missing/implied

---

## §3 — Routing and Cumulative-Dispatch Audit

### Under-Dispatch Findings

**U-1 — PF-3A (Christian Canon Selection): No canonical module**

The anchor case opens with "which Bible version — Protestant or Catholic?" This is a canon-formation question about Christianity, not Islam. RT-2 in `revelation-transmission.md` handles Islamic canon formation. `do-christian-extensions.md` handles Trinity/Incarnation/Philosopher's God. But a Christian interlocutor's uncertainty about their own tradition's canon — deuterocanonical books, Protestant canon, authority of Church councils vs. scripture alone — is NOT addressed by any existing module. V10 would apply in structure but was designed for Islamic transmission vetting. **Result: the practitioner must improvise.**

**U-2 — PF-5 (Doctrinal Complexity): No canonical routing declaration**

The "why do these topics seem complicated?" pattern has no canonical routing declaration. The three-variant structure (inquiry vs. deflection vs. criterion-pressure) is not formally distinguished anywhere. The risk is Diagnosis Collapse — the practitioner jumps to explaining why complexity exists before establishing discourse orientation.

**U-3 — PF-7 (Comparative Prophethood): Opening-frame dispatch not declared**

DO-10, prophecy-wahy-supremacy.md, and DO-4 are all relevant but no file says "for why-Islam-over-religion-X opening frames, dispatch in this sequence." The practitioner must decide the order without architecture.

### Over-Compression Findings

**O-1 — Canon Formation conflation: RT-2 contamination guard mismatch**

RT-2's cross-tradition contamination guard is written from a defensive posture ("don't import NT canon-formation conditions onto Qurʾānic cases"). When the interlocutor is a Christian asking about their own tradition's canon — not attacking Islamic canon — this guard becomes a mismatch. The guard was built for a different direction of pressure.

**O-2 — Family-transfer principle: Not propagated to routing files**

The coverage-ledger.md (corrected in prior session) correctly identifies that V12, deformation types, philosophical-usurpation Types A–D, DO-4, and NS profiles apply cross-tradition through family transfer. But this principle is in the ledger, not in the routing files themselves. V12's routing note says "regardless of interlocutor" (good) but doesn't say "including Hindu polytheism, Buddhist divine-plurality claims, etc." The philosophical-usurpation.md frontmatter has no explicit cross-tradition scope statement.

### Cumulative-Dispatch Findings

**CD-1 — Anchor-case cross-family sequencing unspecified**

For the anchor case's pattern (inherited Christian, pre-inquiry evidentialist demand, canon-confusion, transmission uncertainty, positive restoration framing), the correct cross-family dispatch sequence is:

1. PF-8 (positive restoration — establish register; P1/P4)
2. PF-1 (inherited framework — V2/V7 to loosen inherited filter)
3. FPD (detect whether a foreign criterion is operating)
4. PF-3A or PF-7 depending on which question is most active
5. PF-6 only if Trinity specifically becomes the live issue

No file specifies this cross-family sequence. `mixed-case-handling.md §(iv)` (Inherited-Filter + Evidential Demand) is the closest match but does not address the Christian background or the canon-confusion sub-families.

**CD-2 — DO-11 → DO-12 stopping conditions not explicit**

V12's routing note specifies that DO-11 and DO-12 are sequential (DO-11 first), but no explicit stopping condition says "hold DO-12 until DO-11 has visibly engaged the interlocutor." Anti-pattern: Tactic Over-Selection is the failure mode here — loading V12 + DO-11 + DO-12 + DO-13 simultaneously.

**CD-3 — Dispatch for PF-7 lacks formal stopping conditions between DO-10, DO-4, and prophecy-wahy-supremacy.md**

When the comparative-prophethood family is active, three modules are potentially relevant. No file specifies which takes priority and under what conditions to escalate from DO-4 (religious diversity) to DO-10 (epistemological structure) to specific prophetic credentials.

---

## §4 — Abstraction-Level Audit

### Strong Abstraction (correctly structural)

**A-1 — V12:** Correctly abstracts to "any claim of divine plurality, polytheism, multiple independent deities" — structural trigger, not terminology-dependent. The routing note explicitly includes "philosophical, popular, comparative-religion, or Trinitarian" instances.

**A-2 — foreign-premise-detection.md:** Abstracts to tribunal/criterion/prior-probability/definitional-constraint/background-assumption categories. Near-miss examples are structural, not keyword-triggered.

**A-3 — NS profiles:** Correctly abstract to implicit doxastic rule (NS-1: empirical testability criterion; NS-9: methodological primacy of historical criticism). Phrasings are illustrative, not exhaustive.

### Weak Abstraction (risks literal-wording reliance)

**A-4 — RT-1 through RT-4 worked examples:** Structural patterns are sound but all worked examples are Qurʾānic (Sanaa manuscript, Ḥafṣ vs. Warsh, ʿUthmānic compilation). Given the scope boundary excluding ḥadīth and Bible transmission, this is acceptable, but an explicit note that the structural patterns (provenance → contents → authority) apply to analogous transmission questions in other contexts would improve abstraction without boundary-violation.

**A-5 — V1 specialty-marker list:** The list format ("Historical-critical / manuscript-reconstruction / canon-formation / qirāʾāt-as-variants → revelation-transmission.md") risks being read as exhaustive. "Canon-formation" listed here refers to Qurʾānic canon formation; Christian canon-selection confusion would structurally match but the marker list doesn't say so. GAP-A partially originates here.

**A-6 — PF-5 (doctrinal complexity) abstraction: ABSENT**

Since PF-5 has no canonical owner, there is no abstraction pass at all. The three-variant structure (inquiry / deflection / criterion-pressure) is not formally distinguished anywhere. This is the worst abstraction gap in the repo.

---

## §5 — Ranked Gap List

### Critical (blocks correct routing)

**GAP-A — PF-3A: Christian canon-selection confusion as opening frame has no governed module**
Type: Missing family coverage for a canonical opening pattern
Impact: Anchor case begins with "which Bible version — Protestant or Catholic?" — directly. No module owns this. The practitioner either deflects, loads RT-2 (wrong target), or improvises without architecture.
Patch: `do-christian-extensions.md` — add DO-14 entry; update V1 specialty-marker list; update coverage-ledger.md

**GAP-B — PF-5: Doctrinal complexity has no canonical owner**
Type: Missing family declaration + missing routing rule
Impact: One of the most common opening frames ("why is this complicated?", "too many opinions") has no dispatch guidance. Diagnosis Collapse risk is high — the practitioner defaults to explaining complexity (content) before establishing discourse orientation.
Patch: `mixed-case-handling.md` — add §6 with three-variant decision tree

**GAP-C — Cross-family sequencing for Christian-background pre-inquiry cases unspecified**
Type: Missing cumulative-dispatch routing rule
Impact: Anchor case requires sequencing across PF-8 → PF-1 → FPD → PF-3A or PF-7. No file specifies this for Christian-background cases. `routing-precedence.md` gives axis-level precedence but not family-level sequencing for this compound pattern.
Patch: `mixed-case-handling.md` — add §5 compound playbook

### Significant (degrades precision)

**GAP-D — DO-11 → DO-12 stopping conditions not explicit**
Type: Weak cumulative-dispatch stopping rule within PF-6
Impact: Practitioner loading DO-11 and DO-12 in sequence has no formal stopping guidance. Tactic Over-Selection risk.
Patch: `V12-tamanuc-exhaustion.md` routing section — add stopping condition annotation

**GAP-E — Comparative prophethood "why Islam not another religion" lacks explicit dispatch declaration**
Type: Weak canonical ownership for opening frame
Impact: DO-10, DO-4, and prophecy-wahy-supremacy.md are all relevant but no file declares the canonical sequence.
Patch: `do-core.md` or `do-second-loop.md` — add dispatch declaration for comparative-prophethood opening frames

**GAP-F — Family-transfer principle not propagated to routing files**
Type: Coverage claim (coverage-ledger.md) not reflected in routing guidance
Impact: Practitioner using V12 or philosophical-usurpation.md without reading the ledger won't find the explicit cross-tradition scope statement.
Patch: `V12-tamanuc-exhaustion.md` routing note; `philosophical-usurpation.md` frontmatter

**GAP-G — Ḥadīth authentication: scope boundary declared but no interim routing bridge**
Type: Acknowledged gap with no provisional guidance
Impact: When a ḥadīth-transmission challenge arises, the scope boundary in revelation-transmission.md says "route through NS-9 and V10 principles, noting no dedicated file exists." Practitioner has no interim architecture even in principle.
Patch: `revelation-transmission.md` — add §Ḥadīth Interim Routing section

### Minor (precision polish)

**GAP-H — NS-11 (Fideist) not flagged in compound cases with Christian background**
Type: Thin secondary module consideration
Impact: Anchor case's Christian background could produce NS-11 (fideist — Trinity held on faith, resists rational examination). Not explicitly flagged in mixed-case-handling.md or do-christian-extensions.md routing as a variant that changes the opening move.
Patch: `do-christian-extensions.md` — add NS-11 routing note in DO-11 section

**GAP-I — V1 specialty-marker list risks being read as exhaustive**
Type: Abstraction-level risk
Impact: The format of V1's marker list is illustrative but reads as exhaustive. "Canon-formation" in the list refers to Qurʾānic canon formation; Christian canon-selection would structurally match but isn't listed. Minor after Patch A.
Patch: `V1-diagnostic.md` — add "(illustrative, not exhaustive)" note or add Christian canon-selection to the marker

---

## §6 — File-by-File Patch Plan

### Patch A — do-christian-extensions.md: Add DO-14 (Canon Selection Confusion)

File: `references/case-library/do-christian-extensions.md`
Purpose: Own the "which Bible version — Protestant or Catholic?" opening frame as a governed DO family
Deficiency fixed: GAP-A
Canonical vs. supporting: do-christian-extensions.md becomes canonical owner for PF-3A
Additional changes required:
  - `V1-diagnostic.md`: add "Christian canon-selection / Protestant-Catholic confusion → do-christian-extensions.md DO-14" to specialty-marker list
  - `coverage-ledger.md §3`: add DO-14 row with rating L
  - `coverage-ledger.md §10`: close or reduce Gap 5 (comparative-religion Christian-specific) to note DO-14 governs this sub-family
Terminology change: None new

### Patch B — mixed-case-handling.md: Add §6 (Doctrinal Complexity as Inquiry / Deflection / Criterion-Pressure)

File: `references/diagnostics/mixed-case-handling.md`
Purpose: Name PF-5 as a case family with its three variants and the routing decision tree
Deficiency fixed: GAP-B
Canonical vs. supporting: mixed-case-handling.md becomes canonical owner for PF-5 routing
Additional changes required:
  - `coverage-ledger.md §10`: close Gap for PF-5; add entry under §7 or §9
Terminology change: None new

### Patch C — mixed-case-handling.md: Add §5 (Inherited Christian Framework + Pre-Inquiry Compound Playbook)

File: `references/diagnostics/mixed-case-handling.md`
Purpose: Specify cross-family sequencing for the Christian-background, pre-inquiry, canon-confused compound pattern
Deficiency fixed: GAP-C
Canonical vs. supporting: mixed-case-handling.md as sequencing authority; canonical content stays in family files
Terminology change: None new

### Patch D — V12: Add DO-11 → DO-12 Stopping Conditions

File: `references/techniques/V12-tamanuc-exhaustion.md`
Purpose: Explicit stopping conditions in the Christian-overlay sequencing section
Deficiency fixed: GAP-D
Canonical vs. supporting: V12 owns the sequencing authority
Terminology change: None new

### Patch E — do-second-loop.md: Add Comparative-Prophethood Dispatch Declaration

File: `references/case-library/do-second-loop.md` (or `do-core.md`)
Purpose: Declare canonical dispatch sequence for "why Islam over religion X" opening frames
Deficiency fixed: GAP-E
Additional changes required: `coverage-ledger.md §2` — reflect dispatch ownership
Terminology change: None new

### Patch F — V12 + philosophical-usurpation.md: Add Family-Transfer Scope Statement

Files: `references/techniques/V12-tamanuc-exhaustion.md` (routing note), `references/case-library/philosophical-usurpation.md` (frontmatter/scope)
Purpose: Make the family-transfer principle explicit in routing files, not only in coverage-ledger.md
Deficiency fixed: GAP-F
Terminology change: None new

### Patch G — revelation-transmission.md: Add Interim Ḥadīth Routing Bridge

File: `references/case-library/revelation-transmission.md`
Purpose: After the scope-boundary declaration, add short interim routing guidance for ḥadīth-transmission challenges
Deficiency fixed: GAP-G
Terminology change: None new

---

## §7 — Regression Fixture Suite

### F1 — Anchor Case Pattern (Inherited Christian Framework)

**F1-a** (verbatim anchor): "I was raised as a Christian, I don't have any reason to be Muslim, and I'm not sure which Bible version such as Protestant or Catholic to choose from, or why these topics seem complicated."

Expected routing:
- V1 Phase 1 (listening): attend to register — pre-inquiry, not hostile; Christian background noted
- NS: provisional — NS-12 or NS-7 candidate; cannot assign from thin basis [Excerpt Over-Read anti-pattern active]
- DO-orient: probable truth-seek or zann-mode; insufficient signal for identity-performance
- Concealment: iʿrāḍ candidate (pre-inquiry; nothing pressed against a barrier)
- Deformation: ʿāda candidate (habituated Christian framework); iʿtiqādāt mawrūtha candidate (inherited filter); low confidence on both
- FPD: uncertain (Christian framework functioning as background assumption but no explicit criterion stated)
- Next: P4 (maieutic) or P1 (fiṭrah restoration) — NOT doctrinal content
- Register-hold check: iʿrāḍ + truth-seek/zann matrix → invitational only; V12/DO-11/RT-2 are held
- What NOT to do: load V12 (no active Trinity challenge); load DO-14 prematurely (canon confusion is secondary, not the live barrier); load E1/E3 (no open register for evidential content); assign NS-7 confidently (insufficient signal)

Failure modes tested: Diagnosis Collapse, Forced Fit (NS-7 from "no reason"), Cumulative Inflation (loading all families simultaneously), Tactic Over-Selection, Register-Hold Bypass.

---

**F1-b**: "My family has always been Christian. I'm not sure why I would switch to Islam."

Expected: Strengthens ʿāda + iʿtiqādāt mawrūtha read. "Switch" framing implies possible gharaḍ (social cost if relationships are tied to Christian identity) — but insufficient signal yet. P1/P4 as first move. "Why I would switch" may be opening an evidential-demand frame — note but do not escalate until the question is formed.

---

**F1-c**: "Growing up Christian, I learned that the Bible is God's word. But I've heard Muslims say it was changed. How do I know who's right?"

Expected: PF-4 now active alongside PF-1. "How do I know who's right?" indicates genuine inquiry. DO-orient: truth-seek likely. Deformation: thin — ẓann candidate ("I've heard Muslims say" is second-hand exposure). Route: FPD pass (no explicit criterion; transmission-reliability question is genuine) → V10 → RT-1 (artifact vs. authenticated transmission) framing, noting that Bible-transmission questions are partially governed by RT structural principles but the specifically Christian transmission conditions require careful handling of scope boundary.

---

### F2 — Evidentialist Demand

**F2-a**: "What reason would I have to believe Islam is true?"

Expected: FPD pass first — no explicit criterion stated; uncertain. Check discourse orientation before any evidential content. DO-orient disambiguation required. If truth-seek → E2 (inferential criterion) or P4. If autotelic → relational only. Do not load E1/E3 until criterion status and orientation are determined.

**F2-b**: "Islam needs to pass the same scientific scrutiny as everything else before I'd believe it."

Expected: FPD = detected; Source tradition = scientism/narrow evidentialism; Functional role = criterion; Route consequence = V2 must loosen the criterion before any evidential content. NS-1 candidate. V2 before E1/E3. M1 check: the empirical-testability criterion is not itself empirically testable — self-refutation probe applies before V2.

**F2-c** (verbatim anchor): "I have no religion, I just follow the evidence wherever it leads."

Expected routing:
- Input type: worldview-denial claim → P6 by default
- Claim: authority @ cross-level (meta-epistemic criterion pressure + meta-noetic register question)
- Pattern: PF-2 primary; memetic-profile case, not merely a proposition-level objection; PF-12 candidate only if naturalist filtering later becomes explicit
- NS: NS-2 | NS-1 candidate; do not force a single NS code from the slogan alone
- Reason-category: 3 (pseudo-neutral) candidate; 4 if inherited-milieu language later becomes explicit
- FPD: detected — narrow evidentialism / pseudo-neutral neutrality claim functioning as criterion and tribunal
- Foreign premise consequence: imported criterion-smuggling is active even if the speaker names it as simple openness
- M1 / M1-P: active — the position uses an unnamed ʿaqīdah to deny having one
- Concealment: may read as `irad` when the slogan is functioning as pre-inquiry deflection or register-control rather than contracted inquiry
- Deployment discipline: full internal diagnosis retained; bounded externalization only
- Layer B: one honest question or tightly constrained tribunal-clearing, not a doctrinal dump. Concrete question: "When you say you just follow the evidence, what tells you in advance what is allowed to count as evidence?"
- Boundary reset: if the question lands, do not append E1, E3, DO, or RT content in the same round. Any later content round re-enters through V1 on the new signal.
- What NOT to do: treat the slogan as generic apologetic content demand; collapse the case to proposition-only rebuttal; dump the full P6 / V2 / M1 diagnosis directly at the interlocutor while `irad` remains active

Failure modes tested: fixture loss, forced NS lock, register-hold bypass, current-pass module bleed, proposition-only collapse, rewarded deflection by over-disclosure.

**F2-d**: "I've looked into Islam and I just don't find the arguments convincing."

Expected: Underdetermined — "don't find convincing" could be genuine examination with shubhah (truth-seek), surface dismissal (ẓann), or argument-generation as exit (hawā/gharaḍ). Do NOT load E3 or V6. Mark underdetermined. If the phrase is functioning as a pseudo-neutral tribunal already installed in advance, route it through the same P6 / PF-2 selective branch above; otherwise keep the decisive missing differentiator explicit: what specific arguments were examined and what is the criterion for "convincing"?

---

### F3 — Canon Formation / Text Selection

**F3-a**: "Why do Catholics have extra books in their Bible that Protestants don't?"

Expected: PF-3A live (Christian canon formation as genuine inquiry). Current repo — NO canonical module (GAP-A active). After Patch A → routes to DO-14 in do-christian-extensions.md. Pre-patch: practitioner must note this is outside current canonical coverage and respond from structural principles (authority vs. selection vs. inspiration) without a governed routing architecture.

**F3-b**: "Doesn't the fact that Christians can't agree on their Bible prove that revelation is unreliable?"

Expected: Compound — PF-3A + criterion-pressure (disagreement-implies-unreliability). FPD: criterion = "agreement as test of reliability" — foreign premise detected. V2 on the criterion first. Then, if V2 loosens: Islamic revelation has categorically different transmission conditions. Route: V2 → RT-2 structural principles (authority vs. selection distinction) → DO-14 (after Patch A) for the Christian-specific content.

**F3-c**: "I'm confused about the Qurʾān. Isn't it just a version of earlier scriptures?"

Expected: PF-4 with canon-formation sub-theme. "Version of earlier scriptures" — authority question (RT-2) or originality question (different family). Disambiguate: if "does the Qurʾān depend on prior scriptures for its authority?" → RT-2; if "is the Qurʾān's content derivative?" → different family (revelation, iʿjāz). Do not conflate.

---

### F4 — Comparative Prophethood

**F4-a**: "Why would I believe Muhammad was a prophet if I don't believe Jesus was divine?"

Expected: Theistic framework accepted (not challenging God's existence). Question is prophetic credentials. Route: DO-10 (three-tier structure — Tier 2 is the khabar dimension; this is where prophetic credentials live). Note: the interlocutor's implicit claim that Jesus was not divine means they have already diverged from Trinitarian commitment — this is not a Trinity challenge, it's a prophethood question. DO-10 governs; V12 not triggered.

**F4-b**: "All religions claim to have the truth. Why is Islam's claim any more valid?"

Expected: DO-4 (religious diversity) + DO-10 (epistemological structure). FPD: "all claims are equal" implies relativist background assumption — foreign premise (liberal pluralist framework). V2 to name the assumption; then DO-4; then DO-10 for epistemological structure. Stopping condition: once DO-4 has addressed the relativist challenge, DO-10 provides the positive epistemological structure; prophecy-wahy-supremacy.md for specific credentials thereafter.

**F4-c**: "I respect Muhammad as a historical figure but don't see why he's the final prophet."

Expected: Truth-seek likely; genuine inquiry about prophetic credentials and seal-of-prophets argument. NS-7 or NS-12 candidate. Route: prophecy-wahy-supremacy.md + DO-10 (Tier 2: prophetic claim as khabar). Do not open with DO-4 (religious diversity) — the interlocutor has accepted Muhammad as historical and is asking about the specific "final" claim, not about religious diversity in general.

---

### F5 — Doctrinal Complexity

**F5-a**: "Why is Islam so complicated? There are so many different opinions among scholars."

Expected: PF-5 live. DO-orient disambiguation required first. (a) genuine inquiry → P4; (b) iʿrāḍ using complexity as exit → relational/invitational only; (c) criterion-pressure (disagreement implies falsehood) → V2 on the criterion. Mark underdetermined without further signal. Do NOT explain why Islamic jurisprudential complexity exists until discourse orientation is established.

**F5-b**: "I heard that Muslims can't even agree on basic things. Doesn't that mean nobody really knows?"

Expected: Criterion-pressure variant (PF-5iii). FPD: foreign premise detected ("agreement is the test of knowledge"). V2: the criterion is not self-grounding. After V2: distinction between levels of the tradition (ʿaqīdah agreement vs. fiqh diversity) may be relevant but comes after V2 loosens the criterion.

**F5-c**: "The history of Islamic scholarship is fascinating but I find it overwhelming. Where would I even start?"

Expected: PF-5i + PF-8. "Fascinating" and "where would I start" indicate genuine engagement without hostile framing. DO-orient: truth-seek. Concealment: no iʿrāḍ present. Correct response: P4 / invitational framing + practical orientation. NOT argument. NOT FPD (no criterion detected). This is an invitation, not an objection.

---

### F6 — Christology / Trinity Stopping Conditions

**F6-a**: "If there's one God, how can Jesus be God?"

Expected: V12 first (logical exhaustion of divine plurality — establishes no plurality of independent lords is coherent). Then DO-11 (whether perfect-being reasoning forces multipersonality). Hold DO-12 until DO-11 has been engaged. V8 available alongside if attribute-language issues arise.

**F6-b** (after DO-11 has visibly engaged): "Okay, so perfect-being reasoning doesn't force multipersonality. But doesn't the Christian tradition itself require it?"

Expected: DO-11 has landed. Now DO-12 is appropriate (interlocutor has moved from philosophical to authority-based). Load DO-12 (logical problem of three-in-one). The model-identification probe in DO-12 applies.

**F6-c**: "I believe in the Trinity and that's my faith. I don't need to defend it rationally."

Expected: NS-11 (fideist) candidate. DO-orient = identity-performance or zann-mode (fideist closure). Register-hold: if identity-performance confirmed → matrix cell = relational only; hold V12, DO-11, DO-12 entirely. The correct move is NOT to deploy V12 into fideist-closed posture. Relational/invitational register governs.

---

### F7 — Mixed-Case / Compound Routing

**F7-a** (grief + complexity): "I lost my father last year and since then I've been questioning everything. I was raised Muslim but I'm not sure anymore. Why would God let this happen? And why are there so many different opinions about what's allowed?"

Expected: M4 (grief register) governs everything. DO-2 is held. PF-5 is held. No doctrinal content whatsoever until grief register is established. Anti-pattern tests: loading DO-2 immediately (Diagnosis Collapse), loading PF-5 alongside grief (Cumulative Inflation).

**F7-b** (inherited filter + evidential demand): "I've always believed but when my friends challenge me I don't know how to respond. The evidence they give seems convincing."

Expected: PF-1 + NS-8 candidate. "Evidence they give" is a forwarded challenge — foreign criterion belongs to the friends, not the interlocutor. Route: P5 (already-believing — strengthen examined conviction); V7 (symmetric taqlīd check applied to the friends' framework). Do NOT apply V2 to the interlocutor (they are not the evidentialist).

**F7-c** (authority fatigue + comparative religion): "I was Muslim but I'm not sure anymore. Now I'm reading about Christianity and the love of Jesus seems more appealing."

Expected: NS-8 + possible NS-3 (deconverting). Concealment: hawā candidate (affective pull governs, not intellectual examination). DO-orient: unclear. Register-hold: if hawā confirmed → address the hawā before any comparative doctrinal content. M3 (orphaned intuition) may probe what is driving the appeal. Do NOT load V12 or comparative prophethood arguments — hawā must be addressed first (S-2 suppression rule: confirmed hawā suppresses shubhah engagement).

---

### F8 — Non-Christian Comparative Religion (Family Transfer)

**F8-a**: "I'm Hindu and I believe in many gods. Why would I believe in just one God?"

Expected: V12 applies (base procedure — "any interlocutor"; divine plurality pressure). After V12: check whether the interlocutor's framework is (a) popular Hindu polytheism (multiple independent lords → V12 applies directly) or (b) Advaita monism (one ultimate reality with many manifestations — not polytheism in V12's sense). If Advaita: V12's argument partially applies but the interlocutor would correctly note that Advaita doesn't claim multiple independent lords. This variant requires acknowledging the GAP in bespoke religion-specific coverage (coverage-ledger.md M rating for Advaita-as-rival-ontology).

**F8-b**: "I'm Buddhist and I don't think there needs to be a Creator at all."

Expected: Buddhist dependent-origination as grounds for rejecting a Creator. NS-1 candidate (if operating as a causal-closure equivalent). V2 applies but must be calibrated to Buddhist philosophical framework, not generic scientism — the source tradition in FPD = Buddhist ontology, not scientific naturalism. After V2: DO-10 Tier 1 (fiṭrah delivers recognition that being as such requires a source — this is what the Buddhist dependent-origination account must address). Acknowledge bespoke Buddhist anatta/dependent-origination gap in coverage.

**F8-c**: "I don't really care about religion either way. I just live my life."

Expected: Apatheism. Concealment = iʿrāḍ (matter not allowed to press). DO-orient = autotelic or zann-mode. Matrix cell for iʿrāḍ + autotelic: relational only; no doctrinal module. Correct response: character-as-evidence + one honest question left live + invitation. Nothing from V12, DO-series, or RT-series.

---

## §8 — Final Production-Readiness Judgment

**IMPLEMENTATION STATUS (as of this session):** All patches A through G have been implemented. This section updates the judgment to reflect post-patch state.

---

**POST-PATCH: PRODUCTION-READY**

**Closed gaps (all implemented):**

- **GAP-A (DO-14):** `do-christian-extensions.md` now owns "Christian Canon Selection Confusion" as a governed DO family with a case-profile block, three sub-question discrimination (selection/formation/authorization), prohibited moves (diversity-as-conclusive; RT-2 collapse; premature Islamic answer), positive routing to DO-10 Tier 2 via criterion-gap opening, and NS/deformation pairing. `V1-diagnostic.md` specialty-marker list updated. `coverage-ledger.md` DO-14 row added.

- **GAP-B (§vi in mixed-case-handling.md):** Doctrinal Complexity is now a canonical case-profile routing rule with three structurally distinct profiles (vi-A genuine inquiry / vi-B iʿrāḍ deflection / vi-C criterion-pressure), each with typed case-profile blocks and minimal-pair discriminators. Discourse orientation is the primary axis; content is held if autotelic/iʿrāḍ governs regardless of sophistication of the complexity claim.

- **GAP-C (§v in mixed-case-handling.md):** The Christian-Background Pre-Inquiry compound playbook now activates on structured case-profile, not surface markers. FPD gate is explicit and mandatory before any content module. Sub-question discrimination determines which canonical module applies (DO-14 / RT-1/RT-3 / DO-10/DO-4). Four named failure modes with pass/fail checks: restoration-first collapse, Christology preemption, RT-2 substitution, criterion grant. Fiṭrah-restoration framing (P1/P4) is correctly repositioned as supportive, never substitutive.

- **GAP-D (V12 stopping conditions):** DO-11 → DO-12 sequencing is now governed with explicit stopping conditions, P-3 violation named, and the authority-shift redirect (V10 + RT-2 replaces DO-12 when the interlocutor appeals to tradition rather than philosophy).

- **GAP-E (do-second-loop.md dispatch declaration):** Comparative-prophethood opening-frame dispatch now has a named section with Level 1/2/3 structural dependency (DO-10 → DO-4 → prophecy-wahy-supremacy.md), stopping conditions per level, and a case-profile block including the Christian-background upstream precedence of DO-14 over DO-10.

- **GAP-F (family-transfer propagation):** V12 routing note now carries an explicit cross-tradition scope statement (structural trigger, not tradition-specific; Advaita variant acknowledged with gap notation). `philosophical-usurpation.md` frontmatter now carries the cross-tradition scope (types keyed to framework, not interlocutor background; examples per type).

- **GAP-G (interim ḥadīth routing):** `revelation-transmission.md` now includes a pre-dedicated-file routing section with case-profile discrimination for three ḥadīth-challenge forms (isnād skepticism / āḥād epistemology / historical-critical import), instruments from the current repo, and an explicit architecture-end statement.

**Remaining gaps (still open, correctly bounded):**

- **GAP-H (NS-11 in Christian compound cases):** Minor. NS-11 (fideist) is a variant that can appear in Christian-background cases and changes the opening move (register-hold under identity-performance). The DO-14 entry includes an NS-11 pairing note. The compound playbook in §(v) would benefit from an explicit NS-11 routing note; currently it inherits the register-hold rule from the concealment × orientation matrix. Acceptable as-is.

- **GAP-I (V1 marker list exhaustiveness):** Closed by adding the "(illustrative, not exhaustive)" note and the DO-14 entry. Pattern-recognition primacy over keyword matching is now stated.

- **Bespoke religion-specific families (M, correctly bounded):** Buddhist anatta, Hindu Advaita as rival ontology, Jewish final-prophethood arguments remain ungoverned as bespoke cases. Family-transfer coverage remains operative for cases that instantiate a governed family. No change to this M rating is warranted without dedicated case content.

- **Islamic-specific moral objections (P):** Type D usurpation identification remains L; content depth for specific fiqh-ethics objections remains P. A future DO-15 or NS-8 extension would close this.

- **Ḥadīth authentication content depth (partial C):** Framework routing is now in place (GAP-G closed); the specific epistemological arguments remain absent. Status: partial C.

**Profile-patterning correction status:** The regression where mixed Christian-comparative cases collapse into fiṭrah-heavy/restorative/preachy handling is addressed at the routing level by §(v) of mixed-case-handling.md. The four named failure modes (restoration-first, Christology preemption, RT-2 collapse, criterion grant) are explicit with pass/fail checks. Cumulative dispatch is now governed by FPD output and sub-question identification rather than surface resemblance to "Christian background."

---

## §8 - Third-Wave Acceptance Fixtures

These fixtures do not repeat the first-wave census. They lock down the residual selective-state
transitions that were still too easy to preserve in prose while losing in practice.

### TW-1 - Governed Recursive Continuation

Prompt: "Only empirically testable claims count as knowledge. And if that standard fails on itself, that still doesn't get you to God."

Expected:
- first pass: M1 or V2 may expose the self-undermining rule, but that landing does not authorize same-pass sprawl
- alignment state after the first landed move: `tribunal-loosened` or `recognition-surfaced`, not automatically `alignment-advanced`
- recognition strength: `medium` or `strong` only if the interlocutor actually grants the collapse, accurately restates it, or asks the next sincere question from inside the cleared frame
- continuation eligibility: `blocked` unless a fresh differentiating signal now reopens V1 with the restoration target still unmet
- Layer B: stop at the landed move or leave one bounded question alive; do not append E1, V5, or positive theism merely because M1/V2 landed

### TW-2 - Same-Message Fresh Round

Prompt: "Yeah, that standard isn't neutral. So what would count as a non-imported criterion?"

Expected:
- the tribunal-clearing move has landed strongly enough for Stop-2
- recognition strength: `strong`
- alignment state: at least `recognition-surfaced`; possibly `frame-cleared`, but not `alignment-advanced` unless positive willingness to inhabit the restored order is also visible
- the second sentence is a differentiating signal inside the same message that reopens V1
- continuation eligibility: `eligible-on-refresh`
- next move: the smallest refreshed move justified by the new burden, not the carried-forward prior chain

### TW-3 - Mixed Truth-Seeking Plus Concealment

Prompt: "I do want the truth, but I still don't want Islam to be right."

Expected:
- mixed truth-seeking plus aversion / concealment
- let the stronger present cue govern; do not flatten the case to either pure sincerity or pure concealment
- default Layer B sequence: one bounded diagnostic question first; if the aversion remains the active blocker, add only minimal tribunal-clearing or named register work; then pause
- full internal diagnosis may preserve concealment possibility, restoration target, and held routes, but Layer B does not dump doctrinal content

### TW-4 - Cross-Domain Return to Restoration

Prompt: "The manuscript question may not defeat transmission, but why should that make revelation authoritative?"

Expected:
- V10 or RT clarification may have landed, but the new burden is now authority rather than reconstruction
- alignment state after the first landing: `tribunal-loosened` or `frame-cleared`, not final alignment
- refresh the case-state, then hand off to the next governing authority route rather than continuing RT explanation from momentum
- Layer B: one refreshed authority-facing move only; do not replay provenance, contents, and authority all over again in the same pass
