---
id: routing-precedence
module_class: governance
canonical_path: skill/references/diagnostics/routing-precedence.md
contract_version: "0.3.1.0"
load_when:
  - multiple diagnostic axes produce competing signals
  - suppression rules needed to prevent invalid routing combinations
  - tie-break required between equally-weighted routes
routing_effects:
  - establishes deterministic owner order
  - applies suppression rules S-1 through S-8
  - applies route-priority rules P-1 through P-5
emits:
  - routing_gate
blocks:
  - simultaneous dispatch of competing routes without precedence resolution
  - downstream content release before upstream-blocker route clears
catalogue_registered: false
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

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
5a. **Load-bearing noetic node.** When authority order, epistemic criterion, or validation order is upstream, it is selected as the load-bearing node over any downstream ontological, doctrinal, fiqh, prooftext, or metaphysical hinge. Do not select the downstream topic as primary while the noetic structure governs the case.
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

**Rule S-8:** Upstream load-bearing nodes suppress downstream topic release. If the live node is an authority rule, epistemic criterion, validation order, semantic hinge, or category-set, downstream doctrinal, fiqh, prooftext, or metaphysical content is held until that node is addressed. Tradition labels do not override this rule.

**Rule S-9 (source-status / noetic-frame non-equivalence):** Use
`recursive-state-transitions.md` notation: `N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡
N_Wahhābī`; `N_Ashʿarī[*]` and `N_Māturīdī[*]` are family labels, not automatic operative
`N`; `σ_context != σ_warrant`. Local consequence: one selected operative noetic frame governs
the burden-cycle; non-operative source-status (`contrast`, `opponent-position`, `historical
note`, `genealogy`, `held material`, `bounded comparison`) cannot become warrant without
explicit reclassification. Suppress umbrella and intra-school flattening when the claim is
school-sensitive or disputed.

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

**Rule P-1a (pattern-first, module-fallback):** Optional IR pattern-print fields may identify the local shape of the case, but owner selection still falls back to existing modules. Pattern-first means diagnosis is governed by the live deformation/concealment/warrant disorder actually present in the noetic structure rather than by superficial denomination/topic/source labeling. Named denomination/source identity is never sufficient to route content: `Pattern(deformation/concealment/unsoundness) > denomination/source-label`. It is not abstract universalism, does not mean arbitrary pattern-analysis generates truth, and does not flatten traditions into interchangeable instances of one neutral comparative system. Restoration remains ordered toward sound fitrah, sound reason, revelation, and their non-contradictory ordered convergence. Similar inherited forms or overlapping diagnostic features may be compared only as diagnosis requires; divergent roots, warrant, criterion, authority-order, source, function, or noetic structure remain distinct. A closed-canon veto routes through FPD/V10/RT/DO-10 before any Jewish-specific content; kashf-as-tribunal routes through FPD/usurpation/NS-8 before any Sufism-specific content; Arya Samaj-style "reason/common sense" routes through FPD/V2/reason-disambiguation before any Hindu-specific content; Advaita or anatta pressure routes through M9/V9/metaphysical-architecture as structure permits, without claiming bespoke owner coverage.

**Rule P-2 (case-state-justified coordination):** Among modules that address the same layer, select only the coordination the current validated case-state actually warrants. This may be one module or a layered cluster when distinct live burdens genuinely require it. Within a released live burden, routing must be burden-complete: materially necessary sub-burdens receive matched TTP/operator treatment before `R`; no headline-only answer, skipped internal sub-burdens, generic prose substitute, or broad-conclusion jump may license `NewB`. Burden-complete means owner-specific exit criteria have produced a cumulative-state delta, not merely that every relevant owner was named.

**Rule P-2a (current-pass activation):** `Matched modules` records only the modules whose governing work is active in the present pass. Diagnosed downstream routes that are held by register, semantic, or stop governance stay explicit as held; they do not become ambient simultaneous loads.

**Rule P-2b (current live burden, not route chain):** Routing precedence selects `B`, not
a route itinerary. `FPD -> M1 -> DO-8 -> M8 -> restoration` may describe internal owner
coordination after the fact, but it must not be `Current bounded operator` or the recursion
plan. The selected current burden should read as a function: `imported-criterion tribunal
test`, `worship-worthiness criterion test`, `hujjah/accountability correction`, or another
existing owner-backed function.

**Rule P-3 (no stacking after landing / boundary reset):** Once a module has produced visible recognition or movement, Stop-2 governs the current pass. No additional module is deployed from momentum alone. Any later round re-enters from refreshed V1 rather than inheriting the previous active set by default. A fresh round may be opened by a later reply or by a clear differentiating signal within the same message, its accompanying propositions, or its entailments, but only when the restoration target remains unmet and no stop, register-hold, or semantic gate remains live for the next move. Canonical state-transition model for STOP / HOLD / RECURSE / PARTIAL: `references/diagnostics/recursive-state-transitions.md`.

**Rule P-4 (register before content):** When the concealment x orientation matrix indicates a register-hold, no content module is loaded into Layer B regardless of how strong the NS or deformation read is. The diagnosed downstream route remains explicit in Layer A / the diagnostic IR as held, not discarded or treated as simultaneously active.

**Rule P-5 (refresh before downstream release):** After an upstream load-bearing node clears, refresh the IR state before releasing downstream content. If the downstream burden remains live and no stop, register-hold, semantic gate, or source-use gate blocks it, release only the next bounded move. Do not dump all downstream material because one upstream node cleared.

**Rule P-6 (operative submoves stay inside the burden):** `B -> {s1...sn} -> Land(B)
-> R`. Gloss: multiple TTP operative submoves may be needed to land one selected live
burden. They do not become burden-cycles merely because they are FPD, M1, DO-8, M8,
source-status clarification, restoration framing, or another recognizable route leg.
Submoves also do not multiply without limit. Before a fourth major operative submove is
released, run the submove saturation gate: the next submove must share the same target-family,
claim-level, source/noetic frame, claim cluster, and restoration vector, and it must be
materially necessary for the current burden landing. If that cohesion fails, route to `Land(B) -> R`
before releasing more material.

**Rule P-7 (TTP entry before activation):** Routing precedence does not activate a TTP because
the TTP is topically adjacent. The TTP must satisfy entry criteria: validated IR, owner-backed
selection, bounded target, release permission, and no active stop/hold/gate. If those criteria
are absent, the route remains held or unresolved. After the TTP exits, the next TTP is selected
only from refreshed state, not from an inherited initial route itinerary.

For hard/multi-burden execution, owner-backed selection requires loadform evidence: the
selected owner body or compiled bundle section is loaded/available before `B.s<i>` renders.
`matched_modules` and TTP labels are routing metadata, not proof that the owner floor loaded.
If the owner cannot be loaded or identified, return `PARTIAL / OWNER-BODY-NOT-LOADED`
instead of compressing the burden into generic prose.

**Rule P-7a (owner-specific exit before recursion):** A TTP exit is not valid until the
owning file's minimum operation floor has been executed and its state-change condition is
known. A named operator with generic prose, a route label, or a summary result cannot make
the next route eligible. NewB requires the NewB license test in `recursive-state-transitions.md`.

**Rule P-7b (family floor fallback):** `Family Execution Floor`, `Family Release Floor`,
and `Diagnostic Execution Floor` apply whenever the loaded owner lacks a bespoke floor.
The family floor is still a runtime gate: labels do not execute, classification does not
land a burden, and case-library recognition does not release an answer bank.

**Rule P-7c (V12 independence gate):** V12 is released only when independent-lordship,
multiple-sovereign, or worship-status plurality pressure is live. If independence is
unclear, model/predication discipline runs first and V12 remains held.

**Rule P-8 (operative-frame discipline):** `family label != operative N`;
`shared vocabulary != shared warrant`; `verbal agreement != operative support`;
`σ_context != σ_warrant` unless explicitly reclassified. `N_AT` aliases are one operative
frame, not a prestige stack. Authoritative wording is in
`recursive-state-transitions.md §Source-Status & Noetic-Frame Non-Equivalence Discipline`.

---

## VI. Connection to the Framework Pipeline

This file specifies the rules that govern the routing branches shown in `framework-pipeline.md`. The ASCII chart shows the branching structure; this file specifies the logic at each branch point. `recursive-state-transitions.md` owns the abstract post-render state decision after a bounded move.

---

## VII. Routing Precedence vs. Output-Release Rubric

Routing precedence (§I–§V above) governs owner order: which file addresses the case first, which suppression rules apply, which upstream blocker takes priority. It answers: *what runs and in what order?*

The output-release rubric (`references/rubrics/output-release.md`) governs visible release order and amount. It runs after routing and owner selection. It answers: *how much of what routing selected may be visibly released now, given the current case-state?*

The diagnostic render contract (`references/rubrics/diagnostic-render-contract.md`) governs visible structure. It answers: *is this default compact DSL/IR, `:dsl` concise IR, or internal/development audit compatibility?*

A lower-priority downstream route may be named as held in the routing output but must not be released in the visible response until the higher-priority route has cleared. The held downstream route remains live in Layer A / the IR.

**Cumulative-build rule:** `X -> R(H,Δ) -> Decision`. Gloss: X governs first;
Y stays live/held; Z remains downstream. After X lands, refresh state. If Y remains live
and unblocked, Y becomes the next bounded pass; otherwise drop or compress it. Each refresh
must record cumulative-state delta: what X changed, why Y is now materially different from X,
and why Y was not already answered as an internal submove.

**Anti-smuggling rule:** naming held content in a template field is not holding it. Do
not use lab-report sections or downstream fields to release what routing keeps held.

## Coverage Verification

- Failure condition: If two live axes produce competing routes and no suppression, tie-break, or priority rule is applied, routing has failed even if each selected module is valid in isolation.
- IR-visible consequence: Populate the routing gate, matched/held modules, and "what is withheld and why" so downstream content remains auditable rather than silently dropped or released.
- Minimal pair: A true same-level tie uses T-rules; an upstream-blocker case uses P-1 and holds downstream content until the blocker clears.
- Hold/release rule: Held downstream routes stay live in Layer A and are released only after refreshed state shows the higher-precedence blocker has cleared.
- Anti-pattern guard: Do not smuggle held content through a diagnostic-render field or a "for completeness" aside.
