# TODO

This file tracks unresolved future work for daee-epistemics. It is the single canonical location for future-work items.

Historical audit/task/gap files are not duplicated here where they remain durable:
- `skill/references/diagnostics/pattern-family-audit.md` — pattern-family regression suite and ranked gap list
- `skill/references/diagnostics/proof-method-audit.md` — proof-family audit surface

Current packaged-skill coverage and scope are represented by module front matter, `skill/references/diagnostics/module-catalogue.json`, routing indexes, and explicit owner/router scope notes. The retired coverage ledger is not a current source of truth.

---

## Active

No active unresolved technical pass is currently assigned. The only remaining open items require human scope/source decisions.

---

## Needs Human Review

### Bespoke religion-specific families — scope and content decision
- Status: needs-review
- Source: current needs-review scope boundary; no dedicated owner in `module-catalogue.json` or routing indexes
- Why uncertain: Bespoke argument structures remain outside governed current scope: Buddhist anatta/no-soul as direct challenge to the Islamic account of the nafs; Buddhist impermanence as rival account of creation/divine constancy; Hindu non-dualist (Advaita Vedanta) as rival theological ontology; Jewish final-prophethood argument grounded in Torah's self-characterization as complete. Cross-tradition family-transfer coverage is operative (C rating) for cases that instantiate a governed family. The bespoke gap is for argument structures requiring religion-specific content that cannot be resolved through family transfer. Adding these requires dedicated case files and a scope decision about whether they belong in the current SKILL.md activation scope.
- Research framing note: external source-audit material and its integration plan now provide structural framing seeds, not coverage. They support pattern-first recognition for Jewish Torah-completeness, Hindu Arya Samaj Qur'an critique, Advaita pressure, and Buddhist anatta/impermanence pressure while preserving the needs-review scope boundary. Hindu Arya Samaj should be tracked separately from Advaita if it is ever brought into scope.
- Decision needed: Decide whether to expand SKILL.md activation scope to include these bespoke families explicitly.
- If in scope: Author dedicated case files from authorized comparative-religion sources; add them to coverage-scope.yaml; update SKILL.md, routing/index files, module-catalogue if dispatched, and coverage validation.
- If out of scope: Add an explicit scope-exclusion note to SKILL.md/README or the relevant router explaining that only family-transfer cases are governed.

### Sufism-related crises — scope decision
- Status: needs-review
- Source: current needs-review scope boundary; no dedicated Sufism owner in `module-catalogue.json` or routing indexes
- Why uncertain: Contested Sufi practices and ṭarīqah authority claims are not governed and not explicitly in SKILL.md activation scope. They could arise in NS-8 Muslim-internal cases. Whether these belong in scope requires a deliberate decision before any content is written.
- Research framing note: external source-audit material supplies structural distinctions for kashf-as-tribunal, tariqah authority, wali criteria, authority wound vs authority tribunal, and vocabulary discipline. These are integrated only as IR framing intelligence unless a later task approves a bounded NS-8 owner.
- Decision needed: Determine whether Sufism-related crises fall within current activation scope or should remain outside this skill.
- If in scope: Perform a source-audit pass before writing; create a dedicated case family or NS-8 subroute with failure conditions, IR consequences, discriminators, and hold/release rules.
- If out of scope: Add an explicit scope-exclusion note to `skill/SKILL.md`, NS-8, or the case-library router so public scope claims cannot imply coverage.

---

## Resolved / Consolidated

### Tactic direct-read verification (E/M/R/F + auxiliary)
- Status: resolved
- Source: tactic file front matter and `skill/references/tactics/INDEX.md`
- Resolution: Sessions 17–18 directly read and patched all 24 tactic files. Tactic L(~) bucket: 0.

### Procedure direct-read verification (P1-P5)
- Status: resolved
- Source: procedure file front matter and `skill/references/procedures/INDEX.md`
- Resolution: Session 19 directly read and patched P1-P5. P6 and P7 were already L(✓). Procedure L(~) bucket: 0.

### Coverage-validation direct-read closure
- Status: resolved
- Source: module front matter, `module-catalogue.json`, routing indexes, and explicit owner/router scope notes
- Resolution: Session 20 upgraded remaining NS profile and governance/restoration L(~) rows to L(✓), corrected stale DO-15 and V10 public/router references, and moved non-covered bespoke religion/Sufism claims to explicit needs-review scope status.

### GAP-A: Christian canon-selection confusion as opening frame (DO-14)
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-A
- Resolution: DO-14 implemented in `skill/references/case-library/do-christian-extensions.md`; V1-diagnostic.md specialty-marker list updated. (Session 3)

### GAP-B: Doctrinal complexity has no canonical owner (PF-5)
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-B
- Resolution: `mixed-case-handling.md §(vi)` added with three-variant decision tree (vi-A genuine inquiry / vi-B iʿrāḍ deflection / vi-C criterion-pressure). (Session 3)

### GAP-C: Cross-family sequencing for Christian-background pre-inquiry cases
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-C
- Resolution: `mixed-case-handling.md §(v)` added (generalized to any inherited-tradition background in Session 4). FPD gate and sub-question discrimination explicit. (Session 3–4)

### GAP-D: DO-11 → DO-12 stopping conditions not explicit
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-D
- Resolution: Stopping conditions added to `V12-tamanuc-exhaustion.md`. P-3 violation named. Authority-shift redirect to V10 + RT-2 specified. (Session 3)

### GAP-E: Comparative prophethood dispatch declaration absent
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-E
- Resolution: Comparative-prophethood opening-frame dispatch section added to `do-second-loop.md` with DO-10 → DO-4 → prophecy-wahy-supremacy.md sequence, structural dependencies, and stopping conditions. (Session 3)

### GAP-F: Family-transfer principle not propagated to routing files
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-F
- Resolution: Cross-tradition scope statement added to `V12-tamanuc-exhaustion.md` routing note and to `philosophical-usurpation.md` frontmatter. (Session 3)

### GAP-G: Ḥadīth transmission — no interim routing bridge
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-G
- Resolution: Interim routing section added to `revelation-transmission.md`. Full canonical owner `hadith-authentication-epistemology.md` landed in Session 8. (Session 3, Session 8)

### GAP-I: V1 specialty-marker list reads as exhaustive
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-I
- Resolution: "(illustrative, not exhaustive)" note added to V1-diagnostic.md; DO-14 added to marker list. (Session 3)

### Ḥadīth authentication epistemology (Gap 6 in earlier ledger)
- Status: resolved
- Source: `skill/references/diagnostics/hadith-authentication-epistemology.md`, `skill/references/techniques/V10-transmission-content-vetting.md`, and `skill/references/case-library/revelation-transmission.md`
- Resolution: `hadith-authentication-epistemology.md` now governs corpus skepticism, method skepticism, report-class/epistemic-yield questions, grade confusion, and mixed misuse. RT family remains Qurʾānic-scoped. (Session 8)

### Register-Hold Bypass failure detection (Resolved Check 2)
- Status: resolved
- Source: `skill/references/diagnostics/case-state-schema.md` and `skill/references/diagnostics/anti-patterns.md`
- Resolution: Concealment × orientation matrix in `case-state-schema.md` and named anti-pattern `Register-Hold Bypass` in `anti-patterns.md` aligned. (Session 2)

### Mode-of-concealment file direct-read verification (Gap 7)
- Status: resolved
- Source: `skill/references/diagnostics/modes-of-concealment.md`
- Resolution: `modes-of-concealment.md` directly read and hardened in Session 9. Worldview-deflection / pseudo-neutrality added as first-class concealment-to-deployment route. (Session 9)

### Source-brand cleanup (Volume 1–4 / Taymiyyah references)
- Status: resolved
- Source: files named in the resolution
- Resolution: Branding cleanup performed across do-core.md, do-second-loop.md, do-christian-extensions.md, sound-reason-epistemology.md, terminology.md, fitrah-perspectives.md, ns-8-muslim-internal-crisis.md, and case-library/INDEX.md. No operative source-brand dependency remains. (Session 5)

### Pre-release version-reference cleanup
- Status: resolved
- Source: README.md
- Resolution: Earlier pre-release version prose was removed from README before the v0.2.2.0 release. Current release notes live in `CHANGELOG.md`; README no longer carries release-scope changelog prose.

### Operative front matter rollout — all module classes
- Status: resolved
- Source: `skill/references/diagnostics/operative-contracts.md` §Migration Strategy
- Resolution: YAML operative front matter added to all module classes. technique (V1–V12 + heuristics, Session 15), tactic (all E/M/R/F + auxiliary, Session 15), procedure (P1–P6, Session 15), diagnostic (6 catalogue files, Session 16), case-library (18 files: do-core, do-second-loop, do-christian-extensions, noetic-profiles, philosophical-usurpation, revelation-transmission, ns-1 through ns-12, Session 16), governance (25+ files: framework-pipeline, diagnostic-ir, anti-patterns, case-state-schema, noetic-reading-checklist, mixed-case-handling, output-release, diagnostic-render-contract, seven-deformations, modes-of-concealment, discourse-orientation, reason-disambiguation, foreign-premise-detection, arabic-backbone-predicates, kalamic-interlocutor, pattern-profiling, fitrah-perspectives, inference-boundary, operative-contracts, retired coverage-ledger tombstone, metaphysical-architecture, prophecy-wahy-supremacy, kernel-thesis, module-codes, sound-reason-epistemology, terminology, INDEX files, Session 16). Total: ~99 files changed across both sessions.

### V-series direct-read verification
- Status: resolved
- Source: V-series file front matter and `skill/references/techniques/INDEX.md`
- Resolution: V1–V12 all directly read in Session 16 against L standard (failure conditions, IR-visible consequences, minimal-pair discriminators). Current V-series owner status is represented by the owner files and techniques index. (Session 16)

### Gap 1: Conversation-excerpt minimum-basis rule (noetic-reading-checklist.md)
- Status: resolved
- Source: `skill/references/diagnostics/noetic-reading-checklist.md`
- Resolution: `noetic-reading-checklist.md` §"Thin-Basis / Excerpt Mode" replaced with structured minimum-basis rule: three-dimension convergence requirement (Dimensions 1, 4, 8), explicit provisional-fields list, mandatory decisive-missing-differentiator field, failure test. (Session 15)

### Gap 3: DO-3 through DO-10 failure-test blocks
- Status: resolved
- Source: `skill/references/case-library/do-core.md` and `skill/references/case-library/do-second-loop.md`
- Resolution: Failure-test blocks added to DO-3–DO-6 in `do-core.md` and DO-7–DO-10 in `do-second-loop.md`. All ten entries now L (✓). (Session 15)

### Gap 4: Islamic-specific moral objections (DO-15)
- Status: resolved
- Source: `skill/references/case-library/do-second-loop.md`
- Resolution: DO-15 (Islamic-Specific Moral Objections / Imported-Criterion Form) added to `do-second-loop.md`. Full entry: FPD + Type D usurpation + V2 mandatory sequencing; Level A / Level B moral-claim distinction; four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma); conditions-application analysis; M4 affective-register gate; NS-8/NS-4 pairing; named collapse-move failure tests. (Session 15)

### GAP-H: NS-11 routing note in mixed-case-handling.md §(v)
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §8
- Resolution: NS-11 routing note added to `mixed-case-handling.md §(v)`: fideist-closed inherited-Christian background triggers register-hold before any DO, V12, or RT content; DO-14 and DO-10 held until register shifts from fideist-closed to inquiry-open. (Session 15)
