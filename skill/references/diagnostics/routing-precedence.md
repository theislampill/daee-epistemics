> role: cross-axis precedence encoding
> use when: multiple diagnostic axes produce competing or ambiguous routing signals, or when a routing decision must be justified rather than inferred from prose description
> do not use when: the case is unambiguously single-axis and the matched module is clear
> output: deterministic precedence rules for the defined diagnostic state-space — supersedes prose description where the rules conflict

# Routing Precedence — Cross-Axis Rules

The skill operates on seven independent diagnostic axes: NS (noetic structure), deformation, concealment mode, discourse orientation (DO-orient), claim-type, RT marker, and reason-category. These axes interact. When they produce competing routing signals, the rules below determine which signal takes precedence. Rules are numbered for reference. Where a rule governs, prose-level judgment is not a substitute.

The concealment × orientation routing matrix (in `case-state-schema.md`) handles two axes. This file handles the remaining cross-axis interactions and provides the full precedence hierarchy.

---

## I. Global Precedence Hierarchy

When multiple axes compete, apply in this order:

1. **Concealment mode (if non-clear):** When concealment is confirmed as `irad`, `juhud`, `istikbar`, or `inkar`, the register constraint from that mode gates all other routing. Content cannot be deployed until the register the concealment mode requires is established, regardless of what the deformation, NS code, or DO entry would otherwise imply.

2. **Discourse orientation (if non-truth-seek):** When DO-orient is `identity-perf`, `autotelic`, or `zann-mode`, the matched content module is held. The orientation must shift before the module is deployed.

3. **Deformation (outside-in sequence):** Within the register permitted by concealment mode and DO-orient, deformations are addressed outside-in. ʿĀda before iʿtiqādāt mawrūtha; gharaḍ and hawā before any intellectual content; iʿtiqādāt mawrūtha before evidence; shubhah last.

4. **Reason-category (for content gate):** When reason-category is 3 (pseudo-neutral) or 4 (inherited criterion), V2 is required before content. When reason-category is 2 (corrupted), the volitional deformation is addressed before reason-engagement.

5. **Foreign-premise status:** When a foreign premise is detected functioning as criterion or tribunal, V2 runs before content. This is parallel to reason-category 3/4 — both gate content deployment; a detected foreign premise triggers V2 even if reason-category was marked as sound.

6. **NS code (for content selection):** Only after axes 1–5 are clear does the NS code govern what content is selected. The NS code identifies *what to say*; axes 1–5 identify *whether to say it yet*.

7. **DO code (for argument family):** The DO entry is loaded last — after NS, after register is clear, after deformation sequence is correct. DO is the final content layer, not the entry point.

8. **RT marker (parallel to DO):** RT codes run parallel to DO codes. When an RT marker is active, V10 is applied to the transmission layer before the DO entry is loaded for the doctrinal layer.

---

## II. Suppression Rules

These rules specify when one axis suppresses or delays another:

**Rule S-1:** Non-truth-seeking DO-orient suppresses all doctrinal content modules. No case-library file (noetic-profiles.md, do-core.md, etc.) may be opened while `identity-perf`, `autotelic`, or `zann-mode` governs the orientation.

**Rule S-2:** Confirmed hawā or gharaḍ suppresses shubhah engagement. Even when a genuine shubhah is present alongside hawā/gharaḍ, the shubhah is not engaged until the volitional layer is addressed. The emission order `hawa | shubha` reflects this: hawā must clear before the shubhah gets the instrument.

**Rule S-3:** Underdetermined case-state (read-status: underdetermined) suppresses module selection. When confidence is `low` and read status is `underdetermined`, no module is loaded for the whole-case read. Only the specific claim-type stated is addressed; the governing read is explicitly provisional.

**Rule S-4:** Non-contractual status suppresses depth. When Stop 5 is active (non-contractual inquiry), the full matched module set is suppressed regardless of how clear the NS code and deformation read are. A single well-anchored response is the output ceiling.

**Rule S-5:** Active P7 stop suppresses the corresponding operation. Each P7 stop, when triggered, suppresses a specific type of output until its exit criterion is met. Content-Withholding Stop suppresses argument into grief/identity-performance. One-Live-Question Stop suppresses follow-up content after a landed move. Relational-Repair-First Stop suppresses intellectual content until relational register is established. Underdetermined-Case Stop suppresses confident diagnosis. Non-Contractual-Inquiry Marker suppresses depth beyond a single response.

---

## III. Precedence Tie-Break Rules

When two axes appear to compete at the same precedence level:

**Rule T-1 (concealment tie):** When two concealment modes are genuinely co-present (emission `<mode-A> | <mode-B>`), the more restrictive register governs. `juhud` is more restrictive than `irad` (juhud requires naming the barrier; irad requires invitation — leading with barrier-naming when irad is present hardens the turning-away). When in doubt, apply the more restrictive register and re-assess after one exchange.

**Rule T-2 (deformation tie):** When two deformations are present and their interventions conflict (e.g., gharaḍ requires relational engagement; iʿtiqādāt mawrūtha requires V2), address the outer layer first. Gharaḍ and hawā are always outer layers; iʿtiqādāt mawrūtha is always inner. The Compound Case section of seven-deformations.md fixes the sequence; this rule enforces it when ambiguity arises.

**Rule T-3 (claim-type tie):** When the case presents two claim-types and both appear live (e.g., logical + moral, or historical + authority), identify which one is doing the *governing* work — which one would, if addressed, change the state of the engagement. Address that one first. The secondary claim-type is not ignored; it is deferred until the primary has been addressed.

**Rule T-4 (RT + DO tie):** When both RT pressure and a DO objection are live, V10 runs before the DO entry. The transmission question governs what authority the content carries; the doctrinal question is addressed only after the transmission layer is vetted.

---

## IV. Invalid Combinations

These axis combinations are diagnostic red flags — they indicate a misread or a forced routing rather than a genuine case:

| Combination | Why it is invalid | Correct action |
|-------------|-------------------|----------------|
| `juhud` + `truth-seek` DO-orient + content module deployed | Juhūd bars content deployment; full truth-seeking orientation is incompatible with juhūd's register requirement | Re-run V1; re-assess concealment read; if juhūd is confirmed, hold content module |
| `underdetermined` read-status + `strong` confidence | These fields are defined to be mutually exclusive | Mark one or the other; if basis is thin, confidence cannot be strong |
| Shubhah as sole deformation + P7 Stop 1 active | Stop 1 fires for grief/identity-performance; genuine shubhah does not trigger Stop 1 | Re-check whether the stated shubhah is actually covering a volitional deformation |
| NS code assigned + discourse orientation `autotelic` | Autotelic orientation means the engagement is not aimed at truth; an NS code characterizes epistemic structure, which requires some level of genuine orientation toward the question | Mark NS as provisional or omit pending orientation shift |
| DO-series content loaded + concealment `irad` | Iʿrāḍ means the interlocutor has not given the matter attention; loading DO content pre-supposes the matter has been allowed to press | Invitational register only; DO content held until attention is given |

---

## V. Route-Priority Rules (When Multiple Modules Are Live)

When the case-state has been established and multiple modules could plausibly be deployed:

**Rule P-1 (upstream-blocker priority):** The module that addresses the upstream blocker takes priority over the module that addresses the derived problem. V2 before evidence; F2 before intellectual content; V10 before DO entry; Stop conditions before matched modules.

**Rule P-2 (smallest matched subset):** Among modules that address the same layer, select the smallest subset that changes the next live differentiator. Three well-matched modules outperform nine plausibly relevant ones.

**Rule P-3 (no stacking after landing):** Once a module has produced visible recognition or movement, Stop 2 fires. No additional module is deployed until the interlocutor has re-entered the exchange. This is absolute.

**Rule P-4 (register before content):** When the concealment × orientation matrix indicates a register-hold, no content module is loaded regardless of how strong the NS/deformation read is. Register-hold = deployable only after shift. This is stated in the matrix; this rule restates it as a routing-precedence rule so it is enforced across both files.

---

## VI. Connection to the Framework Pipeline

This file specifies the rules that govern the routing branches shown in `framework-pipeline.md`. The ASCII chart shows the branching structure; this file specifies the logic at each branch point. Use the pipeline chart for structural audit; use this file for the decision rules at each node. They are complementary surfaces of the same decision architecture.
