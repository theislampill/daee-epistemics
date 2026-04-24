---
id: routing-precedence
module_class: governance
canonical_path: skill/references/diagnostics/routing-precedence.md
contract_version: "0.2.0.0"
load_when:
  - multiple diagnostic axes produce competing signals
  - suppression rules needed to prevent invalid routing combinations
  - tie-break required between equally-weighted routes
routing_effects:
  - establishes deterministic owner order
  - applies suppression rules S-1 through S-7
  - applies route-priority rules P-1 through P-4
emits:
  - routing_gate
blocks:
  - simultaneous dispatch of competing routes without precedence resolution
  - downstream content release before upstream-blocker route clears
catalogue_registered: false
---

> role: cross-axis precedence encoding
> use when: multiple diagnostic axes produce competing or ambiguous routing signals, or when a routing decision must be justified rather than inferred from prose description
> do not use when: the case is unambiguously single-axis and the matched module is clear
> output: deterministic precedence rules for the defined diagnostic state-space

# Routing Precedence - Cross-Axis Rules

The skill operates on seven primary diagnostic axes: NS, deformation, concealment mode, discourse orientation (DO-orient), claim-type, RT marker, and reason-category. Two governance overlays also shape routing when emitted: `claim_level` and `pattern_profile` from `pattern-profiling.md`. This file governs their interactions when they produce competing routing signals. The concealment x orientation matrix in `case-state-schema.md` handles two axes directly; this file handles the remaining cross-axis interactions and the full precedence hierarchy.

---

## I. Global Precedence Hierarchy

When multiple axes compete, apply in this order:

1. **Concealment mode (if non-clear and presently stronger).** When concealment is confirmed as `irad`, `juhud`, `istikbar`, or `inkar`, the register constraint from that mode normally gates all other routing. In mixed truth-seeking plus concealment cases, do not treat concealment as automatically absolute; use the stronger present cue rule below.
2. **Discourse orientation (if non-truth-seek and presently stronger).** When DO-orient is `identity-perf`, `autotelic`, or `zann-mode`, the matched content module is held until orientation shifts. When genuine inquiry is stronger in the present exchange, use the smallest permissible move rather than flattening the case into a total hold.
3. **Deformation (outside-in sequence).** `ada` before `i'tiqadat mawrutha`; `gharad` and `hawa` before any intellectual content; `i'tiqadat mawrutha` before evidence; `shubha` last.
4. **Reason-category (content gate).** When reason-category is 3 or 4, V2 is required before content. When reason-category is 2, the volitional deformation is addressed before reason-engagement.
5. **Foreign-premise status.** When a foreign premise is detected functioning as criterion or tribunal, V2 runs before content even if reason-category was marked as sound.
6. **Semantic-discipline gate.** When semantic neutralization of prophetic discourse or a loaded lexical-ontological trap is live, doctrinal content is held until the semantic problem is cleared. This gate does not erase foreign-premise or tribunal findings; it runs after criterion detection and before doctrinal release.
7. **Claim-level (higher-order priority).** When `claim_level` is `meta-epistemic`, `meta-ontological`, `meta-noetic`, or `cross-level`, clear the higher-order burden before first-order case content is released.
8. **NS code (content selection).** Only after steps 1-7 are clear does the NS code govern what content is selected. The NS code identifies what to say; the earlier steps identify whether to say it yet.
9. **DO code (argument family).** The DO entry is loaded after NS, after register is clear, and after the correct upstream sequence has run.
10. **RT marker (parallel to DO).** RT codes run parallel to DO codes. When an RT marker is active, V10 is applied to the transmission layer before the DO entry is loaded for the doctrinal layer. When the transmission burden is ḥadīth-authentication rather than RT-1..RT-4, V10 and `hadith-authentication-epistemology.md` occupy this slot without emitting a new RT code.

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

**Rule T-6 (mixed truth-seek + concealment tie):** When truth-seeking signals and concealment or aversion signals coexist, let the stronger present cue govern the immediate Layer B move. Default sequence: ask one bounded diagnostic question first; if the answer keeps the blocker live, add only minimal tribunal-clearing; then pause. Full doctrinal release is not licensed merely because some sincerity is visible.

---

## IV. Invalid Combinations

These combinations are diagnostic red flags:

| Combination | Why invalid | Correct action |
|-------------|-------------|----------------|
| `juhud` + `truth-seek` DO-orient + content module deployed | `juhud` bars content deployment | Re-run V1; if `juhud` is confirmed, hold content module |
| `irad` + `truth-seek` DO-orient + content module deployed | `irad` means the matter has not yet been allowed to press | Hold content module; use invitational register and one honest question |
| `underdetermined` read-status + `strong` confidence | These fields are mutually exclusive | Mark one or the other |
| `Shubha` as sole deformation + P7 Stop-1 active | Stop-1 fires for grief or identity-performance, not genuine `shubha` | Re-check whether the stated `shubha` is covering a volitional deformation |
| NS code assigned + discourse orientation `autotelic` | Autotelic orientation means the engagement is not aimed at truth | Mark NS as provisional or omit pending orientation shift |
| DO-series content loaded + concealment `irad` | `irad` means the matter has not been allowed to press | Invitational register only; DO content held |
| `semantic-neutralization-*` or `lexical-ontological-trap` active + `Routing gate: open` | Semantic discipline is an upstream blocker | Set `Routing gate: semantic-discipline-required`; run the owning file first |
| `Routing gate: register-hold` + `What is withheld and why` absent | Register-hold without an explicit hold statement is incomplete governance; the held route becomes invisible to audit | Populate `What is withheld and why` in the IR before dispatching any response |
| `Continuation eligibility: eligible-on-refresh` + `What remains live` absent | Eligible-on-refresh without naming the open axis or unmet target is an unanchored refresh permission | Populate `What remains live` with the specific restoration gap or differentiating signal that justifies the refresh |

---

## V. Route-Priority Rules

When the case-state has been established and multiple modules could plausibly be deployed:

**Rule P-1 (upstream-blocker priority):** The module that addresses the upstream blocker takes priority over the module that addresses the derived problem. V2 before evidence; semantic-discipline owner before doctrinal release; higher-order claim-level owner before first-order case content; F2 before intellectual content; V10 before DO entry; stop conditions before matched modules.

**Rule P-2 (case-state-justified coordination):** Among modules that address the same layer, select only the coordination the current validated case-state actually warrants. This may be one module or a layered cluster when distinct live burdens genuinely require it.

**Rule P-2a (current-pass activation):** `Matched modules` records only the modules whose governing work is active in the present pass. Diagnosed downstream routes that are held by register, semantic, or stop governance stay explicit as held; they do not become ambient simultaneous loads.

**Rule P-3 (no stacking after landing / boundary reset):** Once a module has produced visible recognition or movement, Stop-2 governs the current pass. No additional module is deployed from momentum alone. Any later round re-enters from refreshed V1 rather than inheriting the previous active set by default. A fresh round may be opened by a later reply or by a clear differentiating signal within the same message, its accompanying propositions, or its entailments, but only when the restoration target remains unmet and no stop, register-hold, or semantic gate remains live for the next move. Canonical state-transition model for STOP / PAUSE / RECURSE: `references/diagnostics/framework-pipeline.md §Recursive State-Transition View`.

**Rule P-4 (register before content):** When the concealment x orientation matrix indicates a register-hold, no content module is loaded into Layer B regardless of how strong the NS or deformation read is. The diagnosed downstream route remains explicit in Layer A / the diagnostic IR as held, not discarded or treated as simultaneously active.

---

## VI. Connection to the Framework Pipeline

This file specifies the rules that govern the routing branches shown in `framework-pipeline.md`. The ASCII chart shows the branching structure; this file specifies the logic at each branch point.

---

## VII. Routing Precedence vs. Output-Release Rubric

Routing precedence (§I–§V above) governs owner order: which file addresses the case first, which suppression rules apply, which upstream blocker takes priority. It answers: *what runs and in what order?*

The output-release rubric (`references/rubrics/output-release.md`) governs visible release order and amount. It runs after routing and owner selection. It answers: *how much of what routing selected may be visibly released now, given the current case-state?*

The diagnostic render contract (`references/rubrics/diagnostic-render-contract.md`) governs visible structure. It answers: *is this ordinary prose, compact diagnostic, or full audit render?*

A lower-priority downstream route may be named as held in the routing output but must not be released in the visible response until the higher-priority route has cleared. The held downstream route remains live in Layer A / the IR.

**Cumulative-build rule:**
X governs first; Y is live but held; Z is downstream and not yet released.
After X is addressed, refresh state. If Y remains live and no stop/hold/gate blocks it, Y becomes the next bounded pass. If Y no longer governs, it is dropped or compressed.

**Anti-smuggling rule:**
Do not use a visible lab-report section or a named downstream field to release held content that routing precedence requires to remain held. Naming held content in a template field is not the same as holding it.
