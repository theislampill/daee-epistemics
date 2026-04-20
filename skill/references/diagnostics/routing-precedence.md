> role: cross-axis precedence encoding
> use when: multiple diagnostic axes produce competing or ambiguous routing signals, or when a routing decision must be justified rather than inferred from prose description
> do not use when: the case is unambiguously single-axis and the matched module is clear
> output: deterministic precedence rules for the defined diagnostic state-space

# Routing Precedence - Cross-Axis Rules

The skill operates on seven primary diagnostic axes: NS, deformation, concealment mode, discourse orientation (DO-orient), claim-type, RT marker, and reason-category. Two governance overlays also shape routing when emitted: `claim_level` and `pattern_profile` from `pattern-profiling.md`. This file governs their interactions when they produce competing routing signals. The concealment x orientation matrix in `case-state-schema.md` handles two axes directly; this file handles the remaining cross-axis interactions and the full precedence hierarchy.

---

## I. Global Precedence Hierarchy

When multiple axes compete, apply in this order:

1. **Concealment mode (if non-clear).** When concealment is confirmed as `irad`, `juhud`, `istikbar`, or `inkar`, the register constraint from that mode gates all other routing.
2. **Discourse orientation (if non-truth-seek).** When DO-orient is `identity-perf`, `autotelic`, or `zann-mode`, the matched content module is held until orientation shifts.
3. **Deformation (outside-in sequence).** `ada` before `i'tiqadat mawrutha`; `gharad` and `hawa` before any intellectual content; `i'tiqadat mawrutha` before evidence; `shubha` last.
4. **Reason-category (content gate).** When reason-category is 3 or 4, V2 is required before content. When reason-category is 2, the volitional deformation is addressed before reason-engagement.
5. **Foreign-premise status.** When a foreign premise is detected functioning as criterion or tribunal, V2 runs before content even if reason-category was marked as sound.
6. **Semantic-discipline gate.** When semantic neutralization of prophetic discourse or a loaded lexical-ontological trap is live, doctrinal content is held until the semantic problem is cleared. This gate does not erase foreign-premise or tribunal findings; it runs after criterion detection and before doctrinal release.
7. **Claim-level (higher-order priority).** When `claim_level` is `meta-epistemic`, `meta-ontological`, `meta-noetic`, or `cross-level`, clear the higher-order burden before first-order case content is released.
8. **NS code (content selection).** Only after steps 1-7 are clear does the NS code govern what content is selected. The NS code identifies what to say; the earlier steps identify whether to say it yet.
9. **DO code (argument family).** The DO entry is loaded after NS, after register is clear, and after the correct upstream sequence has run.
10. **RT marker (parallel to DO).** RT codes run parallel to DO codes. When an RT marker is active, V10 is applied to the transmission layer before the DO entry is loaded for the doctrinal layer.

`pattern_profile` does not outrank the hierarchy. It is a consolidation overlay that helps choose the smallest matched coordination once the higher-precedence blockers have been handled.

---

## II. Suppression Rules

These rules specify when one axis suppresses or delays another:

**Rule S-1:** Non-truth-seeking DO-orient suppresses all doctrinal content modules.

**Rule S-2:** Confirmed `hawa` or `gharad` suppresses `shubha` engagement. Even when a genuine `shubha` is present alongside them, the `shubha` is not engaged until the volitional layer is addressed.

**Rule S-3:** Underdetermined case-state suppresses whole-case module selection. When confidence is `low` and read status is `underdetermined`, no module is loaded for the whole-case read.

**Rule S-4:** Non-contractual status suppresses depth. When Stop-5 is active, the full matched module set is suppressed regardless of how clear the NS code and deformation read are.

**Rule S-5:** Active P7 stop suppresses the corresponding operation.

**Rule S-6:** Semantic-discipline blockers suppress doctrinal release. When `semantic-neutralization-recontenting`, `semantic-neutralization-evacuation`, or `lexical-ontological-trap` is active, the routing gate is `semantic-discipline-required` until the relevant semantic clarification file has run.

**Rule S-7:** Higher-order burdens suppress first-order-only release. When `claim_level` is `meta-epistemic`, `meta-ontological`, or `meta-noetic`, first-order case files are held until the governing higher-order owner has cleared the burden.

---

## III. Precedence Tie-Break Rules

When two axes appear to compete at the same precedence level:

**Rule T-1 (concealment tie):** When two concealment modes are genuinely co-present, the more restrictive register governs.

**Rule T-2 (deformation tie):** When two deformations are present and their interventions conflict, address the outer layer first.

**Rule T-3 (claim-type tie):** When the case presents two claim-types and both appear live, identify which one is doing the governing work and address that one first.

**Rule T-4 (RT + DO tie):** When both RT pressure and a DO objection are live, V10 runs before the DO entry.

**Rule T-5 (tribunal + semantic blocker tie):** When both an imported tribunal and a semantic blocker are live, intervention order is tribunal first, semantic blocker second, doctrinal content third. The semantic blocker remains live after tribunal refusal; do not collapse the case into one label.

---

## IV. Invalid Combinations

These combinations are diagnostic red flags:

| Combination | Why invalid | Correct action |
|-------------|-------------|----------------|
| `juhud` + `truth-seek` DO-orient + content module deployed | `juhud` bars content deployment | Re-run V1; if `juhud` is confirmed, hold content module |
| `underdetermined` read-status + `strong` confidence | These fields are mutually exclusive | Mark one or the other |
| `Shubha` as sole deformation + P7 Stop-1 active | Stop-1 fires for grief or identity-performance, not genuine `shubha` | Re-check whether the stated `shubha` is covering a volitional deformation |
| NS code assigned + discourse orientation `autotelic` | Autotelic orientation means the engagement is not aimed at truth | Mark NS as provisional or omit pending orientation shift |
| DO-series content loaded + concealment `irad` | `irad` means the matter has not been allowed to press | Invitational register only; DO content held |
| `semantic-neutralization-*` or `lexical-ontological-trap` active + `Routing gate: open` | Semantic discipline is an upstream blocker | Set `Routing gate: semantic-discipline-required`; run the owning file first |

---

## V. Route-Priority Rules

When the case-state has been established and multiple modules could plausibly be deployed:

**Rule P-1 (upstream-blocker priority):** The module that addresses the upstream blocker takes priority over the module that addresses the derived problem. V2 before evidence; semantic-discipline owner before doctrinal release; higher-order claim-level owner before first-order case content; F2 before intellectual content; V10 before DO entry; stop conditions before matched modules.

**Rule P-2 (smallest matched subset):** Among modules that address the same layer, select the smallest subset that changes the next live differentiator.

**Rule P-3 (no stacking after landing):** Once a module has produced visible recognition or movement, Stop-2 fires. No additional module is deployed until the interlocutor has re-entered the exchange.

**Rule P-4 (register before content):** When the concealment x orientation matrix indicates a register-hold, no content module is loaded regardless of how strong the NS or deformation read is.

---

## VI. Connection to the Framework Pipeline

This file specifies the rules that govern the routing branches shown in `framework-pipeline.md`. The ASCII chart shows the branching structure; this file specifies the logic at each branch point.
