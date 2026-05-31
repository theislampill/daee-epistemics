# Audit and Release Evidence Index

This index separates current evidence from historical snapshots. It is
navigation, not runtime source. Retention policy lives in
`docs/audits/README.md`.

Archive mode for the v0.4.3.0 pruning pass: no physical moves or deletes. A
reference search found inbound links for the audit corpus, so superseded audits
are archived by classification here unless a future owner-approved link-update
sweep moves them.

## Current Release / Readiness Evidence

| Path | Status | Note |
|---|---|---|
| `docs/release-artifacts.md` | ACTIVE CURRENT TRUTH | Release package/provenance evidence ledger and proof boundaries. |
| `docs/package-smoke-readiness.md` | ACTIVE CURRENT TRUTH | Package-smoke runbook, strict witness gate, and deferred expanded-smoke slots. |
| `docs/v0.4.3.0-release-notes.md` | ACTIVE CURRENT TRUTH | v0.4.3.0 release notes for closure reconstructibility, `field_witness`, visualizer, MRP, proof boundaries, and caveats. |
| `docs/v0.4.3.0-release-log.md` | ACTIVE CURRENT TRUTH | v0.4.3.0 package artifact facts, proof boundary, and release step log. |
| `docs/v0.4.2.0-release-notes.md` | ACTIVE CURRENT TRUTH | v0.4.2.0 release notes with explicit local proof boundaries and deferrals. |
| `docs/v0.4.2.0-release-log.md` | ACTIVE CURRENT TRUTH | v0.4.2.0 release log with local package-bound gate and release-scope caveats. |
| `docs/audits/v0.4.2.0-current-release-smoke-runbook.md` | ACTIVE CURRENT TRUTH | Owner packet for required local package-bound current-release smoke capture. |
| `docs/audits/v0.4.2.0-p0-remediation.md` | ACTIVE IMPLEMENTATION EVIDENCE | Supersedes earlier v0.4.2.0 release-candidate blocker state. |
| `docs/audits/v0.4.2.0-release-candidate-audit.md` | SUPERSEDED BUT KEEP | Historical pre-public snapshot; latest package/smoke status is `v0.4.2.0-p0-remediation.md`. |
| `docs/releases/README.md` | ACTIVE CURRENT TRUTH | Release-doc navigation surface. |

## Current v0.4.3.0 Prep Evidence

| Path | Status | Note |
|---|---|---|
| `docs/audits/v0.4.3.0-skill-entrypoint-cleanup-ab-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Corrected inlined-runtime Smoke E/F proof for SKILL entrypoint cleanup and PACK-SPEC checker hardening. |
| `docs/audits/v0.4.3.0-adhlbs-skill-governance-audit.md` | ACTIVE CURRENT TRUTH | External ADHLBS governance audit; keeps trigger-eval/lifecycle gaps out of runtime bloat. |
| `docs/audits/v0.4.3.0-formalism-pointer-discipline-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Formalism pointer PDCA, Smoke G/H preservation, and local validator hardening. |
| `docs/audits/v0.4.3.0-closure-witness-graph-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Closure witness graph grammar, `field_witness` sidecar, parser/checker, and standalone DAG viewer proof. |
| `docs/audits/v0.4.3.0-mid-reread-pressure-ttp-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | TTP-MRP reread-time activation harness, active `∇·T` / `∇×T` gate, graph/field_witness evidence, fixtures, and checker proof. |
| `docs/audits/v0.4.3.0-reconstructibility-mrp-completion-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Completion audit verifying closure graph, canonical sidecar naming, visualizer modes, MRP, and integrated deterministic proof; live generated-runtime smoke remains unverified. |
| `docs/audits/v0.4.3.0-mrp-codex-hosted-behavior-smoke.md` | ACTIVE RELEASE EVIDENCE | Codex-hosted exact-file hard-compound Smoke 6 proof that MRP is behavioral, inter-burden, and reconstructible rather than ornamental; raw smoke outputs are not release assets. |
| `docs/audits/v0.4.3.0-regression-hold-audit.md` | HISTORICAL RELEASE EVIDENCE | Records the first v0.4.3.0 withdrawal/regression hold; superseded by the repaired hotfix release line. |
| `docs/audits/v0.4.3.0-trinitarian-mrp-hotfix-audit.md` | ACTIVE RELEASE EVIDENCE | Targeted Trinitarian RC2 hotfix evidence for STOP-before-continuation, `∇·T`/`∇×T` route discipline, and mixed-field classification. |
| `docs/audits/v0.4.3.0-mrp-route-curl-generalization-audit.md` | ACTIVE RELEASE EVIDENCE | Generalized route/curl invariant audit with secularism, TST, synthetic fixtures and the boundary that the hosted secularism smoke proves route/curl/field only. |
| `docs/audits/v0.4.3.0-main-reconciliation-audit.md` | ACTIVE RELEASE EVIDENCE | Main/source reconciliation audit proving the repaired v0.4.3.0 release-source invariants were brought back onto main before Output Grapher publication. |
| `docs/audits/v0.4.3.0-output-grapher-branch-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Docs-only Output Grapher branch audit with synthetic fixtures, fresh skill-output reconstruction smokes, export proof, and cold-reader visual review. |
| `docs/audits/v0.4.3.x-mrp-concealment-audit-complement.md` | ACTIVE IMPLEMENTATION EVIDENCE | Complement to the external MRP/concealment audit with corrective real-smoke proof, held/generated MRP lineage, surface-open/framework-concealed concealment discipline, and bounded schema deferrals. |
| `docs/audits/v0.4.3.0-rc1-closeout-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Internal RC1 closeout for v0.4.3.0 reconstructibility/MRP work, local CI-equivalent proof, commit boundary, and live/package proof caveats. |
| `docs/audits/v0.4.3.0-audit-of-audits.md` | ACTIVE IMPLEMENTATION EVIDENCE | Audit-of-audits input and closure for targeted stale-status cleanup. |
| `docs/audits/v0.4.3.0-open-work-ledger.md` | ACTIVE OPEN-WORK LEDGER | Forward formalism/proof work for managing agents after the published v0.4.3.0 asset; records dependency-ordered A/B/C rows that remain open and must not be treated as release notes or as already closed by publication. |
| `docs/audits/v0.4.3.0-retained-smoke-sidecar-convention.md` | ACTIVE IMPLEMENTAUDIT PROCESS GUIDANCE | Checker-owned B.2/B.4 retained-smoke sidecar convention: raw input, collapse certificate, certificate-backed Grapher, hashes, proof boundaries, and scoped exclusions. |
| `docs/audits/v0.4.3.0-future-work-ledger.md` | FUTURE-WORK SOURCE | Single ledger for deferred/tabled findings that should not remain scattered as live blockers. |

## Current Governance / Runtime Evidence

| Path | Status | Note |
|---|---|---|
| `docs/audits/v0.4.2.0-skill-md-dry-acid-ssot-audit.md` | ACTIVE CURRENT TRUTH | SKILL.md DRY/ACID/SSOT/progressive-disclosure audit and owner-pointer plan. |
| `docs/audits/v0.4.2.0-skill-ab-smoke-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Smoke A/B/C/D runtime-load localization and local output validator evidence. |
| `docs/audits/v0.4.2.0-pack-spec-operating-discipline-audit.md` | ACTIVE CURRENT TRUTH | PACK-SPEC and operating-discipline integration and checker scope. |
| `docs/audits/v0.4.2.0-deep-research-coverage-proof.md` | ACTIVE IMPLEMENTATION EVIDENCE | Coverage proof for v0.4.2.0 Deep Research scope. |
| `docs/audits/v0.4.2.0-deep-research-gap-remediation.md` | ACTIVE IMPLEMENTATION EVIDENCE | Gap remediation ledger for Deep Research operativity findings. |
| `docs/audits/v0.4.2.0-underfixtured-module-coverage.md` | ACTIVE IMPLEMENTATION EVIDENCE | Under-fixtured module appendix and follow-up evidence. |
| `docs/audits/v0.4.2.0-fixture-corpus-mining-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Fixture mining record and implemented fixture table. |
| `docs/audits/v0.4.2.0-stale-surface-purge-audit.md` | ACTIVE IMPLEMENTATION EVIDENCE | Stale-surface purge record and proof-boundary classifications. |

## Current Docs/Index Evidence

| Path | Status | Note |
|---|---|---|
| `docs/audits/v0.4.2.0-docs-index-ssot-audit.md` | ACTIVE CURRENT TRUTH | Docs/index source ownership, generated runtime/theory surfaces, and checker coverage. |
| `docs/audits/v0.4.2.0-docs-index-design-md-audit.md` | ACTIVE CURRENT TRUTH | DESIGN.md adoption and docs/index-scoped visual/design ownership. |
| `docs/audits/v0.4.2.0-docs-index-design-quality-audit.md` | ACTIVE CURRENT TRUTH | Durable docs/index design-quality rubric. |
| `docs/audits/v0.4.2.0-docs-index-design-refinement-implementation.md` | ACTIVE IMPLEMENTATION EVIDENCE | Implemented P1 docs/index refinement and Reference Library source-browser follow-up. |
| `docs/audits/v0.4.2.0-docs-index-handoff.md` | ACTIVE CURRENT TRUTH | Tracked mirror of ignored root handoff state for docs/index design work. |
| `docs/audits/v0.4.2.0-docs-index-design-refinement-plan.md` | SUPERSEDED BUT KEEP | Plan snapshot implemented by `v0.4.2.0-docs-index-design-refinement-implementation.md`. |

## Future Work / Deferred Items

Use `docs/audits/v0.4.3.0-open-work-ledger.md` for dependency-ordered formalism,
collapse-certificate, graph-completeness, NLA, and escape-route proof work that
remains pertinent to the v0.4.3.0 line after release publication.

Use `docs/audits/v0.4.3.0-future-work-ledger.md` as the owner for generic tabled
work instead of re-promoting repeated TODOs from historical audits.

| Deferred item | Current owner |
|---|---|
| Formal termination proof / generation-depth / MRP exhaustion lemmas | `docs/audits/v0.4.3.0-open-work-ledger.md` |
| Collapse certificate and graph-completeness checker | `docs/audits/v0.4.3.0-open-work-ledger.md` |
| Certificate-backed Output Grapher extension over existing grapher implementation | `docs/audits/v0.4.3.0-open-work-ledger.md` |
| NLA isomorphism / normalized activation record / reproducibility harness | `docs/audits/v0.4.3.0-open-work-ledger.md` |
| Typed escape-route closure proof | `docs/audits/v0.4.3.0-open-work-ledger.md` |
| Trigger-eval taxonomy | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Retire/revise lifecycle criteria | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Minimum execution load-floor shrink | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Expanded 10-case/generalization smoke suite | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Paraphrase clusters and cross-host probes | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Cross-host/paraphrase MRP proof | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| MRP schema-language cleanup / anti-bloat refinement | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Heuristics/noetic-profiles catalogue migration | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Future package-bound release-smoke proof | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Broad source notation/prose checker | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Generated symbol-owner matrix | `docs/audits/v0.4.3.0-future-work-ledger.md` |
| Docs/index pixel-perfect visual regression helper | `docs/audits/v0.4.3.0-future-work-ledger.md` |

## Historical / Archived Audits

These files are retained for provenance and historical traceability. They should
not be treated as current blockers unless a newer audit explicitly reopens the
finding.

| Path | Status | Superseded by / note |
|---|---|---|
| `docs/audits/audit-history-v0.3.md` | HISTORICAL SNAPSHOT | Consolidated v0.3.2.0 audit/campaign evidence. |
| `docs/audits/audit-history-v0.4.0.0.md` | HISTORICAL SNAPSHOT | Consolidated v0.4.0.0 audit/inventory/smoke evidence. |
| `docs/audits/audit-history-pre-v0.4.1.md` | HISTORICAL SNAPSHOT | Consolidated miscellaneous older audits. |
| `docs/releases/release-history-v0.3.md` | HISTORICAL SNAPSHOT | Consolidated v0.3.x release docs. |
| `docs/releases/release-history-v0.4.md` | HISTORICAL SNAPSHOT | Consolidated v0.4.x release docs. |
| `docs/audits/v0.4.1.0-docs-consolidation-inventory.md` | HISTORICAL SNAPSHOT | Older docs inventory; current index and docs/index audits supersede status. |
| `docs/audits/v0.4.1.0-level3-deprecation-audit.md` | HISTORICAL SNAPSHOT | Older terminology cleanup; current docs/runtime avoid Level 3 as public framing. |
| `docs/audits/v0.4.1.0-pipeline-label-deprecation-audit.md` | HISTORICAL SNAPSHOT | Older pipeline-label cleanup; current generated docs/checks supersede status. |
| `docs/audits/v0.4.1.0-cleanup-readiness-audit.md` | HISTORICAL SNAPSHOT | Older cleanup readiness; v0.4.2/v0.4.3 audits supersede release-line status. |
| `docs/audits/v0.4.1.0-conway-yagni-audit.md` | HISTORICAL SNAPSHOT | Principles carried into operating-discipline docs; no current blocker. |
| `docs/audits/v0.4.1.0-github-ci-release-automation-audit.md` | HISTORICAL SNAPSHOT | Older CI/release automation audit; current release docs/workflows govern. |
| `docs/audits/v0.4.1.0-formalism-operativity-audit.md` | HISTORICAL SNAPSHOT | Current formalism status lives in `v0.4.3.0-formalism-pointer-discipline-audit.md`. |
| `docs/audits/v0.4.1.0-algebraic-symbol-operativity-audit.md` | HISTORICAL SNAPSHOT | Current symbol-owner status lives in `v0.4.3.0-formalism-pointer-discipline-audit.md`. |
| `docs/audits/v0.4.1.0-nla-operativity-audit.md` | HISTORICAL SNAPSHOT | Current formalism/checker status supersedes. |
| `docs/audits/v0.4.1.0-skill-compliance-audit.md` | HISTORICAL SNAPSHOT | Current SKILL status lives in v0.4.2/v0.4.3 SKILL audits. |
| `docs/audits/v0.4.1.0-ttp-operativity-audit.md` | HISTORICAL SNAPSHOT | Current strict TTP checker and later fixture coverage supersede status. |
| `docs/audits/v0.4.1.0-ttp-end-to-end-operativity-audit.md` | HISTORICAL SNAPSHOT | Current strict TTP checker and later fixture coverage supersede status. |
| `docs/audits/v0.4.1.0-ci-release-operativity-audit.md` | HISTORICAL SNAPSHOT | Older CI/release audit; current release docs/workflows govern. |
| `docs/audits/v0.4.1.0-release-claim-inventory.md` | HISTORICAL SNAPSHOT | v0.4.2 release docs and remediation supersede status. |
| `docs/audits/v0.4.1.0-release-claim-integrity-audit.md` | HISTORICAL SNAPSHOT | v0.4.2 release docs and remediation supersede status. |
| `docs/audits/v0.4.1.0-complementary-ssot-pipeline-freshness-audit.md` | HISTORICAL SNAPSHOT | Current generated-runtime/docs checks supersede status. |
| `docs/audits/v0.4.1.0-history-regression-archaeology-audit.md` | HISTORICAL SNAPSHOT | Operating-discipline packs preserve lessons; no current blocker. |
| `docs/audits/v0.4.1.0-docs-index-generator-parity-audit.md` | HISTORICAL SNAPSHOT | Later docs/index SSOT/design audits supersede. |
| `docs/audits/v0.4.1.0-docs-index-source-coupling-audit.md` | HISTORICAL SNAPSHOT | Later docs/index SSOT/design audits supersede. |
| `docs/audits/v0.4.1.0-secular-humanist-field-governance-audit.md` | HISTORICAL SNAPSHOT | Current field/operator checks supersede status. |
| `docs/audits/v0.4.1.0-field-gradient-loop-closure-coupling-implementation-audit.md` | HISTORICAL SNAPSHOT | Current field-operator checker and formalism audit supersede status. |
| `docs/audits/v0.4.1.0-deep-research-implementation-audit.md` | HISTORICAL SNAPSHOT | v0.4.2 Deep Research coverage/gap remediation supersede. |
| `docs/audits/v0.4.1.0-deep-research-next-handoff.md` | SUPERSEDED BUT KEEP | Earlier handoff; v0.4.2 remediation and smoke evidence supersede status. |
| `docs/audits/v0.4.1.0-generated-runtime-untracking-audit.md` | HISTORICAL SNAPSHOT | Generated-runtime policy is now in AGENTS and compiler/checker docs. |
| `docs/audits/v0.4.2.0-deep-research-next-handoff.md` | SUPERSEDED BUT KEEP | Pre-public handoff before later P0 closure; keep as handoff record. |

## Non-Markdown Audit Support

Non-markdown audit support files remain in place and are not active narrative
surfaces by default:

| Path | Status | Note |
|---|---|---|
| `docs/audits/v0.4.1.0-ttp-runtime-contract-remediation.json` | HISTORICAL SNAPSHOT | Machine-readable remediation ledger retained for provenance. |
| `docs/audits/v0.4.1.0-full-history-name-status.txt` | HISTORICAL SNAPSHOT | Git-history name/status support file retained for audit traceability. |
