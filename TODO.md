# TODO

This file tracks unresolved future work for daee-epistemics. It is the single canonical location for future-work items.

Historical audit/task/gap files are not duplicated here — they remain as durable governance references where they exist:
- `skill/references/diagnostics/coverage-ledger.md` — canonical parity audit ledger (§10: gap inventory)
- `skill/references/diagnostics/pattern-family-audit.md` — pattern-family regression suite and ranked gap list
- `skill/references/diagnostics/proof-method-audit.md` — proof-family audit surface

---

## Active


---

### Tactic direct-read verification (E/M/R/F + auxiliary)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §8
- Resolution (Session 17–18): All 24 tactic files directly read. Session 17: 15 upgraded to L(✓); enhanced YAML front matter applied. Session 18: remaining 8 files (E2, M2, M3, M6, R1, R2, R3, F1) patched in-body with §Failure Conditions, §IR-Visible Consequences, §Minimal-Pair Discriminators, §Hold/Release Discipline, §Anti-Pattern Guard. All 24 tactic files now L(✓). Tactic L(~) bucket: 0.

---

## Needs Human Review

### Bespoke religion-specific families — scope and content decision
- Status: needs-review
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Gap 5 and §9
- Why uncertain: Three bespoke argument structures remain M (missing/implied): Buddhist anatta/no-soul as direct challenge to the Islamic account of the nafs; Hindu non-dualist (Advaita Vedanta) as rival theological ontology; Jewish final-prophethood argument grounded in Torah's self-characterization as complete. Cross-tradition family-transfer coverage is operative (C rating) for cases that instantiate a governed family. The bespoke gap is for argument structures requiring religion-specific content that cannot be resolved through family transfer. Adding these requires dedicated case files and a scope decision about whether they belong in the current SKILL.md activation scope.
- Suggested next check: Decide whether to expand SKILL.md activation scope to include these cases explicitly, then assign to a dedicated authoring pass.

### Sufism-related crises — scope decision
- Status: needs-review
- Source: `skill/references/diagnostics/coverage-ledger.md` §9
- Why uncertain: Contested Sufi practices and ṭarīqah authority claims are not governed and not explicitly in SKILL.md activation scope. They could arise in NS-8 Muslim-internal cases. Whether these belong in scope requires a deliberate decision before any content is written.
- Suggested next check: Determine if Sufism-related crises fall within SKILL.md activation scope. If yes, a source-audit pass using Ibn Taymiyyah's primary Arabic treatises on the topic would be the appropriate research approach. If no, add a scope-exclusion note to `skill/SKILL.md` or NS-8.

---

## Resolved / Consolidated

### GAP-A: Christian canon-selection confusion as opening frame (DO-14)
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §5 GAP-A
- Resolution: DO-14 implemented in `skill/references/case-library/do-christian-extensions.md`. V1-diagnostic.md specialty-marker list updated. coverage-ledger.md DO-14 row added. (Session 3)

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
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Resolved Check 6
- Resolution: `hadith-authentication-epistemology.md` now governs corpus skepticism, method skepticism, report-class/epistemic-yield questions, grade confusion, and mixed misuse. RT family remains Qurʾānic-scoped. (Session 8)

### Register-Hold Bypass failure detection (Resolved Check 2)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Resolved Check 2
- Resolution: Concealment × orientation matrix in `case-state-schema.md` and named anti-pattern `Register-Hold Bypass` in `anti-patterns.md` aligned. (Session 2)

### Mode-of-concealment file direct-read verification (Gap 7)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Gap 7
- Resolution: `modes-of-concealment.md` directly read and hardened in Session 9. Worldview-deflection / pseudo-neutrality added as first-class concealment-to-deployment route. (Session 9)

### Source-brand cleanup (Volume 1–4 / Taymiyyah references)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §12 Session 5
- Resolution: Branding cleanup performed across do-core.md, do-second-loop.md, do-christian-extensions.md, sound-reason-epistemology.md, terminology.md, fitrah-perspectives.md, ns-8-muslim-internal-crisis.md, case-library/INDEX.md, and coverage-ledger.md. Only surviving reference is "Volume 1–4" as a session-name label in coverage-ledger.md revision log (safe). (Session 5)

### v0.2.1.0 version references
- Status: resolved
- Source: README.md / coverage-ledger.md
- Resolution: v0.2.1.0 entries folded back into v0.2.0.0 in Session 14. Only surviving reference is a historical note in coverage-ledger.md current-pass note explaining the fold. (Session 14)

### Operative front matter rollout — all module classes
- Status: resolved
- Source: `skill/references/diagnostics/operative-contracts.md` §Migration Strategy
- Resolution: YAML operative front matter added to all module classes. technique (V1–V12 + heuristics, Session 15), tactic (all E/M/R/F + auxiliary, Session 15), procedure (P1–P6, Session 15), diagnostic (6 catalogue files, Session 16), case-library (18 files: do-core, do-second-loop, do-christian-extensions, noetic-profiles, philosophical-usurpation, revelation-transmission, ns-1 through ns-12, Session 16), governance (25+ files: framework-pipeline, diagnostic-ir, anti-patterns, case-state-schema, noetic-reading-checklist, mixed-case-handling, output-release, diagnostic-render-contract, seven-deformations, modes-of-concealment, discourse-orientation, reason-disambiguation, foreign-premise-detection, arabic-backbone-predicates, kalamic-interlocutor, pattern-profiling, fitrah-perspectives, inference-boundary, operative-contracts, pattern-family-audit, coverage-ledger, metaphysical-architecture, prophecy-wahy-supremacy, kernel-thesis, module-codes, sound-reason-epistemology, terminology, INDEX files, Session 16). Total: ~99 files changed across both sessions.

### V-series direct-read verification
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §8
- Resolution: V1–V12 all directly read in Session 16 against L standard (failure conditions, IR-visible consequences, minimal-pair discriminators). All 12 entries upgraded from L(~) to L(✓) in coverage-ledger.md §8. §9 stale entries also corrected (conversation excerpt P → L(✓), DO-8 L(~) → L(✓)). (Session 16)

### Gap 1: Conversation-excerpt minimum-basis rule (noetic-reading-checklist.md)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Gap 1
- Resolution: `noetic-reading-checklist.md` §"Thin-Basis / Excerpt Mode" replaced with structured minimum-basis rule: three-dimension convergence requirement (Dimensions 1, 4, 8), explicit provisional-fields list, mandatory decisive-missing-differentiator field, failure test. (Session 15)

### Gap 3: DO-3 through DO-10 failure-test blocks
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Gap 3
- Resolution: Failure-test blocks added to DO-3–DO-6 in `do-core.md` and DO-7–DO-10 in `do-second-loop.md`. All ten entries now L (✓). (Session 15)

### Gap 4: Islamic-specific moral objections (DO-15)
- Status: resolved
- Source: `skill/references/diagnostics/coverage-ledger.md` §10 Gap 4
- Resolution: DO-15 (Islamic-Specific Moral Objections / Imported-Criterion Form) added to `do-second-loop.md`. Full entry: FPD + Type D usurpation + V2 mandatory sequencing; Level A / Level B moral-claim distinction; four-foundations criterion (ʿadl / raḥma / maṣlaḥa / ḥikma); conditions-application analysis; M4 affective-register gate; NS-8/NS-4 pairing; named collapse-move failure tests. (Session 15)

### GAP-H: NS-11 routing note in mixed-case-handling.md §(v)
- Status: resolved
- Source: `skill/references/diagnostics/pattern-family-audit.md` §8
- Resolution: NS-11 routing note added to `mixed-case-handling.md §(v)`: fideist-closed inherited-Christian background triggers register-hold before any DO, V12, or RT content; DO-14 and DO-10 held until register shifts from fideist-closed to inquiry-open. (Session 15)
