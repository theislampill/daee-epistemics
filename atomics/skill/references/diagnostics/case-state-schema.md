---
id: case-state-schema
module_class: governance
canonical_path: skill/references/diagnostics/case-state-schema.md
contract_version: "0.4.0.0"
load_when:
  - any substantive response needs explicit routing state
catalogue_registered: false
---

# Case State Schema

This file governs the internal case-state record and visible case-state rendering when a
diagnostic render is selected. It is not a separate tactic and it is not a default output
template. Default mode is derived from this state internally but does not print the full
`[Case State]` block.

The case-state is the control record derived from the validated Diagnostic IR. In `:dsl`,
`:audit`, pass-review, or diagnostic trace, it may be surfaced to make routing legible and
auditable. In default `/daee-epistemics`, it governs prose without becoming the prose.
It tracks the live noetic configuration as the object of diagnosis, not a paraphrase of the whole discourse.
Use it to keep two things distinct: the noetic structure itself, and the meta-noetic memetic
dynamics shaping it. The former is the operative configuration of commitments, grounding,
testimony, filters, and dependencies. The latter is how whole noetic structures and their
governing epistemic rules form, function, stabilize, defend themselves, mutate, reproduce,
spread, and become linguistically instantiated through recurring slogans, labels, arguments,
habits, and social patterns.

## IR Derivation Map

The `[Case State]` block is the diagnostic-render form of the validated Diagnostic IR. Every
visible field in `:dsl`, `:audit`, pass-review, or diagnostic trace must be traceable to an IR
source. In default mode, these fields remain internal unless a materially necessary distinction
can be compressed into ordinary prose without printing the block. This table is the tracing
protocol.

| Surfaced `[Case State]` field | IR source field | Derivation type |
|-------------------------------|----------------|-----------------|
| `Case family` | `Case family` | direct |
| `Claim-type` | `Claim-type` | direct |
| `Claim level` | `Claim-level` | direct |
| `Reason-category` | `Reason-category` | direct |
| `Foreign-premise status` | `Foreign premise` | direct |
| `Upstream findings` | `Upstream findings` | direct |
| `Primary upstream issue` | `Foreign premise` + `Upstream findings` | surfaced expansion — must not add a diagnosis absent from both IR fields |
| `Pattern profile` | `Pattern-profile` | direct |
| `Primary deformation` | `Deformation` (primary only) | direct |
| `Routing gate` | `Routing gate` | direct |
| `Read status` | `Read status` | direct |
| `Discourse orientation` | `DO-orient` | direct |
| `Concealment mode` | `Concealment mode` | direct |
| `Alignment state` | `Alignment state` | direct |
| `Recognition strength` | `Recognition strength` | direct |
| `Continuation eligibility` | `Continuation eligibility` | direct |
| `Confidence` | `Confidence` | direct |
| `Restoration target` | `Restoration target` | direct |
| `Matched modules` | `Matched modules` | direct |
| `Register-hold` | `Routing gate: register-hold` + `What is withheld and why` | surfaced expansion — populate only when IR has register-hold gate and withheld content |
| `Deployable on shift to` | `What is withheld and why` | surfaced expansion — names the release condition stated in the IR withheld field |
| `Decisive missing differentiator` | `What remains live` | surfaced expansion — names one specific signal from the IR's open-axis list |
| `Post-render gate` | `post_render_gate` | direct — mandatory state re-read / re-entry gate after each bounded move |
| `Cleared this pass` | `post_render_gate.cleared_this_pass` | direct |
| `Remaining live distortions` | `post_render_gate.remaining_live_distortions` | direct |
| `Held routes rechecked` | `post_render_gate.held_routes_rechecked` | direct |
| `Newly released routes` | `post_render_gate.newly_released_routes` | direct |
| `Next eligible pass` | `post_render_gate.next_eligible_pass` | direct |
| `Recursion decision` | `post_render_gate.recursion_decision` | direct — STOP / HOLD / RECURSE / PARTIAL |
| `Live alternatives` | `Read status: distributed` + competing NS/deformation reads in the IR | case-state-schema-native — tracks competing candidate reads alongside underdetermined IR; must not assert a read stronger than the IR's `Read status` |
| `Reassessment` | `Continuation eligibility` + `Alignment state` | case-state-schema-native — states the refresh trigger; must not license continuation the IR's `continuation_eligibility` field has not licensed |
| `Convergence requirement` | `Matched modules` + routing-precedence state | case-state-schema-native — expresses whether multiple non-redundant routes are warranted; must remain consistent with IR-level module selection |
| `Sequencing rationale` | `Matched modules` + `Routing gate` + routing-precedence rules | case-state-schema-native — explains module ordering; must not justify a sequence the IR's routing gate has blocked |

**Governance rule:** A `[Case State]` field populated with content that has no IR source or
diagnostic-render expansion path is improvised output. Improvised output violates `SKILL.md` Rule 7.
If the IR cannot support a field, either (a) populate the IR field first, or (b) leave the
surfaced field blank rather than filling it from prose judgment.

**Default compression rule:** In default mode, do not print the full `[Case State]` block. The
answer may mention only materially necessary distinctions in prose. Omission from visible prose
means the field was checked and either inactive, routine, or not needed for public legibility;
it does not mean the IR was untyped. The internal IR must still carry `Claim-level: first-order`
and `Pattern-profile: none` explicitly when those are the validated values.

## Standard Form

Render-mode scope: this template is an internal control shape and may be visible only in
`:dsl`, `:audit`, pass-review, or diagnostic trace. It is not a default output template.

Use this block only when diagnostic rendering is selected (`:dsl`, `:audit`, pass-review, or
diagnostic trace). It is not the default `/daee-epistemics` output template:

```text
[Case State]
- Case family:
- Diagnostic target:                 # claim / worldview / quoted-interlocutor / requester-self-state / mixed
- Concealment applies to:            # diagnostic-target by default; requester only when self-state is explicitly the target
- Requester posture:                 # if visible; non-diagnostic unless self-state is the target
- Claim-type:
- Claim level:                      # first-order / meta-epistemic / meta-ontological / meta-noetic / cross-level; omit only when routine first-order
- Reason-category:                   # 1 / 2 / 3 / 4 - from reason-disambiguation.md; governs routing gate
- Foreign-premise status:            # detected [premise] / none-detected / uncertain - from FPD pass
- Upstream findings:                 # criterion-import / tribunal-installation / transmission-demotion / semantic-neutralization-recontenting / semantic-neutralization-evacuation / lexical-ontological-trap
- Primary upstream issue:            # must reflect FPD output when criterion-importing is live
- Pattern profile:                   # PF-1 ... PF-12 from pattern-profiling.md when a recurring cross-volume family is governing
- Primary deformation:
- Routing gate:                      # open / V2-required / deformation-first / semantic-discipline-required / register-hold / stop-condition
- Read status:
- Live alternatives:
- Reassessment:
- Convergence requirement:
- Discourse orientation:
- Concealment mode:
- Register-hold:
- Deployable on shift to:
- Matched modules:
- Sequencing rationale:
- Restoration target:                # must name epistemic layer or ontological distinction from metaphysical-architecture.md
- Alignment state:                   # blocked / tribunal-loosened / frame-cleared / recognition-surfaced / alignment-advanced
- Recognition strength:             # none / weak / medium / strong
- Continuation eligibility:         # not-assessed / blocked / eligible-on-refresh
- Confidence:
- Decisive missing differentiator:
- Post-render gate:
- Recursion decision:               # STOP / HOLD / RECURSE / PARTIAL
- Next eligible pass:
```

```text
[Source Basis]
- [anchored]:
- [synthesis]:
- [inference]:
- [speculative]:
- Source type / weight:
- Restoration source:
```

## Field Discipline

- `Case family` names the class of case, not the whole argument history.
- `Claim-level` is required internally when a higher-order burden is visible, when `cross-level` sequencing is needed, or when the full Diagnostic IR is being surfaced in `:dsl` or `:audit`. In narrow routine first-order cases it may be omitted from default prose after the diagnostic pass has found no criterion, category, or noetic-order fight. Omission means "no higher-order burden detected," not "unknown."
- `Reason-category` is required in the internal case-state. Carry `1`, `2`, `3`, or `4` from `reason-disambiguation.md`. The routing gate depends on this field: category 3 or 4 blocks content until V2; category 2 requires deformation-first gate; category 1 leaves the gate open. Do not leave this field blank on any case where intellectual content is being pressed.
- `Foreign-premise status` is required when criterion-importing, tribunal-installation, or framework-importing elements are visible. The `[Foreign Premise Detection]` block from `foreign-premise-detection.md` feeds this field. If FPD was not run and this field is blank, the `Primary upstream issue` field cannot be reliably populated.
- `Upstream findings` is the compact owner hook for upstream burdens that must stay live across passes without collapsing into one label. Use only the canonical tags named in the standard form. When both an imported tribunal and a semantic-discipline problem are live, include both tags and let `Sequencing rationale` state the intervention order rather than erasing one into the other. This is also the surfaced home for tribunal installation, semantic capture, and related meta-noetic pressures when they are doing routing work.
- `Primary upstream issue` must reflect FPD output when a foreign premise is live. Stating "the interlocutor doubts X" is not an upstream issue; naming the specific criterion, tribunal, prior probability assignment, or interpretive filter that is generating the objection is.
- `Pattern profile` is optional but strongly preferred when a recurring PF family is governing the next move. Keep one primary profile only; carry competing profiles in `Live alternatives`.
- `Primary deformation` should name only the deformation governing the next move.
- `Concealment mode` is required. Use `clear` when no active concealment mode is positively
  read; use `mode-?` only when the axis remains genuinely unresolved after attention to the
  concealment read. Do not leave this field blank and do not substitute placeholders such as
  `none confirmed`. Surface openness is not enough for `clear`: when an imported framework,
  pseudo-neutral tribunal, or identity-stabilizing lens is operative, the concealment axis
  remains non-clear unless that lens has been positively exposed and no longer governs the
  current pass. Non-clear diagnoses must name a source-owned mode from
  `modes-of-concealment.md` (`irad`, `juhud`, `inkar`, `istikbar`, `nifaq`, or `mixed`);
  descriptive glosses such as framework-concealed or predicate-concealed are secondary notes,
  not replacements for the mode.
- Sincere clarification pressure is adjacent to, not identical with, concealment/refusal mode.
  If a Muslim/ḥanīf/truth-seeker is under shubhah, shakk/rayb, tawahhum, or doubt-pressure
  without visible refusal, render the pressure explicitly (`clarification pressure: shubha /
  shakk-rayb`, or `Concealment mode: clarification / shubha pressure` in public prose). This
  means "no refusal mode is operative," not "no occlusion or burden exists."
- `Diagnostic target`, `Concealment applies to`, and `Requester posture` prevent target leakage.
  Generic refutation or analysis prompts diagnose the claim/worldview/quoted interlocutor by
  default. Do not attach `iʿrāḍ`, `juḥūd`, `inkār`, `istikbār`, `nifāq`, or `mixed` to the
  requester unless the requester explicitly makes their own state the diagnostic target.
- `Register-hold` is required whenever concealment x orientation blocks direct deployment.
  It names the axis or cell doing the holding. This field governs Layer B only; it does not
  cancel the Layer A diagnosis.
- `Deployable on shift to` is required whenever `Register-hold` is populated. Name the shift
  that would release held content rather than implying the content vanished.
- `Routing gate` is required whenever any upstream blocker remains live. Use `semantic-discipline-required` when semantic neutralization or a loaded lexical-ontological trap must be cleared before doctrinal content can be released.
- `Restoration target` must name what epistemic layer (`fitrah` / sound reason / authentic transmission / inferential argument) or ontological distinction (`creator-creation` / `transcendence-immanence` / `prophetic-authority`) is being restored. A target stated as "demonstrate divine unity" or "correct the objection" has not reached the restoration level. The aim is restorative structural viability, not merely a correct sentence.
- `Alignment state` is required whenever the response is doing explicit routing work beyond a routine first-order case. Use `blocked` when the governing filter still controls the case; `tribunal-loosened` when the imported criterion has visibly lost its neutrality claim; `frame-cleared` when the subject can now examine signs, revelation, or transmission without the old filter governing; `recognition-surfaced` when a landed move has produced medium or strong visible uptake; and `alignment-advanced` only when positive recognition and willingness to inhabit the restored order are visibly present. `tribunal-loosened` and `frame-cleared` are real progress, but they do not yet equal `alignment-advanced`.
- `Recognition strength` is required whenever a move has landed enough to raise the Stop-2 question. Use `none`, `weak`, `medium`, or `strong`. Weak signals include politeness, silence, irritation, or rhetorical concession without state-shift. Medium and strong signals are what govern Stop-2 and refreshed continuation.
- `Continuation eligibility` is required whenever the question is whether to continue, pause, or stop after a landed move. Use `not-assessed` before that question is live; `blocked` when a stop, hold, gate, or satisfied restoration target forbids more release; `eligible-on-refresh` only when a fresh differentiating signal has reopened V1, the restoration target remains unmet, and no stop, register-hold, or semantic gate remains live for the next move.
- `Claim-type` identifies the governing logical category of the live pressure: `logical`, `metaphysical`, `moral`, `historical`, `transmission`, `phenomenological`, or `authority`. Record the primary type only. Carry any secondary type in `Live alternatives`, `[Core Formulation]`, or `What remains live`.
- `Read status` should be `dominant`, `distributed`, or `underdetermined`.
- `Live alternatives` should stay short. Keep live alternatives, not a full inventory. Preserve only routes that remain structurally live after the present correction; do not keep already-collapsed dependencies in circulation as though they still governed the case.
- `Reassessment` should say `not warranted`, `revisit after X`, or `warranted now because Y`. A fresh differentiating signal may arise in a later reply or inside the same message through an accompanying proposition or entailment; if so, say that explicitly.
- `Convergence requirement` should say whether one dominant move remains preferable or whether convergence across independent routes is now needed to advance the restoration target rather than merely win an argumentative point.
- `Matched modules` should list only the current-pass, case-state-justified coordination: the modules whose governing work is active now. Do not use this field as a memory of every plausible file or every downstream owner that may later become relevant.
- When a register-hold, semantic blocker, or stop keeps downstream content from deployment, keep that route explicit in `Register-hold`, `Deployable on shift to`, or the restoration trace's `What was withheld and why`; do not pad `Matched modules` with held-later content.
- `Sequencing rationale` should explain sequencing, not restate file names.
- `Confidence` should be marked as `strong`, `provisional`, or `low`.
- `Decisive missing differentiator` should name the one signal that would collapse the remaining ambiguity.
- `[Source Basis]` is the companion diagnostic-render block used when the reply combines files or needs explicit source-status marking. In default mode, keep source-status internal or integrate a compact source note only when it materially improves the answer; do not print a source-basis ledger. Omit empty lines rather than filling every marker slot performatively.
- `Source type / weight` is optional. Use it when unlike materials are joined or when a lighter source is being used only for sequencing, illustration, or operational reminder rather than for the core doctrinal or epistemic claim.
- `Restoration source` is optional. Use it when the positive picture is being drawn from a clearly anchored higher-weight source rather than from free synthesis.

## Restoration Trace Block

Use this block after the matched-module response is complete. It records the restorative logic, not just the argumentative content. Omit when the case is too thin for restorative work to have been performed, or when the routing was entirely routine.

```text
[Restoration Trace]
- Governing misread risk:
- What was withheld and why:
- What correction was applied:
- Route that became permissible after correction:
- What remains live or unresolved:
```

Field discipline:

- `Governing misread risk` names the single most likely wrong module or wrong register the case would route to without the diagnostic gate.
- `What was withheld and why` names the module(s) held in reserve and the governing reason. It preserves Layer A intelligibility; it does not authorize Layer B preview.
- `What correction was applied` names the specific restorative move made.
- `Route that became permissible after correction` names the immediate next route only. Do not use this field to emit a queued future stack.
- `What remains live or unresolved` names any open axis, unconfirmed deformation, live alternative, or load-bearing dependency whose removal would reopen or collapse downstream routes.

Compression rule: populate only the fields that had operative content. A restoration trace with two populated fields is more honest than one that fills all five performatively. If no correction was required, omit the block entirely.

Integration with `[Source Basis]`: the restoration trace is downstream of the case-state and source-basis blocks. It does not replace them. Case-state names what was diagnosed; source-basis names where claims are grounded; restoration trace names what was done to create the conditions under which the response could land.
Boundary reset rule: once a move lands or Stop-2 fires, later deployment must be re-justified from the current case-state. Held routes do not become deployable automatically, but they do carry forward as held until explicitly released, resolved, skipped, or marked PARTIAL. A fresh round may be opened by a later reply or by a clear differentiating signal inside the same message, its accompanying propositions, or its entailments, but only when the refreshed case-state still shows an unmet restoration target and no stop, register-hold, or semantic gate bars the next move.

## Post-Render Gate Block

Visible block format is `:audit` / diagnostic-trace only. In default mode this gate runs
internally and renders only as prose transition or clean STOP/PARTIAL wording when needed.

Use this block after every bounded restorative move before STOP, HOLD, RECURSE, or PARTIAL is
declared when diagnostic rendering is selected. It is the diagnostic-render form of the IR
`post_render_gate`; in default mode the state re-read must exist internally and any same-response
RECURSE must be visible through a short prose transition, not through this block.

```text
[Post-Render Gate]
- Cleared this pass:
- Remaining live distortions:
- Held routes rechecked:
- Newly released routes:
- Next eligible pass:
- Recursion decision: STOP | HOLD | RECURSE | PARTIAL
```

Field discipline:

- `Cleared this pass` names the bounded move that actually landed; do not restate the whole response.
- `Remaining live distortions` names same-input live pressure after the move. Use `none` only when none remains.
- `Held routes rechecked` names the previously held routes that were tested after refresh; use an empty list only when no routes were held.
- `Newly released routes` names only routes whose release signal is now present. If any are present, STOP is invalid.
- `Next eligible pass` names the next bounded pass or explicitly says `none`.
- `Recursion decision` governs closure: STOP only when no live distortion or newly eligible held route remains; HOLD when live material is still blocked; RECURSE when another bounded pass is eligible; PARTIAL when limits prevent eligible continuation.

## Strength Rules

- Mark `strong` only when multiple indicators align across noetic structure, deformation, and discourse behavior.
- Mark `provisional` when the read is plausible but still driven by partial signals.
- Mark `low` when only a thin surface objection is available and major routing dimensions remain open.

## Compression Rule

Do not narrate every field in every answer. Surface only the fields that improve governance, legibility, or trust in the selected render mode. The point is disciplined visibility, not transparency theater.

Surface-mode policy:

- **Default mode:** do not print the full `[Case State]`, `[Source Basis]`, `matched_modules`, route plan, or post-render ledger. Render governed prose from the internal state and mention only the distinctions needed for the bounded answer.
- **DSL mode:** compact case-state may appear when it improves routing legibility; show only governing fields rather than the full audit ledger.
- **Audit mode:** when the task is audit-facing, analytic, or explicitly asks for architecture visibility, surface the richer state directly from the validated IR: `claim level`, `pattern profile`, `routing gate`, `alignment state`, `recognition strength`, `continuation eligibility`, current-pass `matched modules`, and one brief theory-to-routing bridge when it materially clarifies the live route.
- The modes change surfaced explicitness, not internal discipline. The internal IR stays fully typed in all modes.

## Concealment x Orientation Routing Matrix

Concealment mode and DO-orient compose orthogonally. The matrix is the fastest way to see which register the case belongs to before the doctrinal module is loaded. The matched-module choice from the NS + deformation axis is almost always correct at the level of content; the matrix answers whether the content is deployable now or waits on a register shift.

| Concealment \\ DO-orient | `truth-seek` | `identity-perf` | `autotelic` | `zann-mode` | `mixed` |
|--------------------------|-------------|-----------------|-------------|-------------|---------|
| clear | Full apparatus. Load matched module. | Name the register first; doctrinal module waits on register shift. | Do not feed; leave one question live; do not mistake for shubha. | Press one specific claim at a time; suspend larger moves. | Lead with the predominant orientation; note the minority channel. |
| `irad` | Let the stronger present cue govern. If truth-seeking is genuinely stronger, ask one bounded diagnostic question first. If the answer keeps the blocker live, add only minimal tribunal-clearing and then pause. If aversion is stronger, stay invitational and do not dump argument. Character-as-evidence remains primary. | `irad` compounded by identity performance hardens under argument. Relational only; no doctrinal module. | Expected compound; do not feed; do not mistake for shubha. | Do not press claims; the matter has not been allowed to press. Invitation first. | Re-enter after attention stabilizes. |
| `juhud` | Argument will not land. Character-as-evidence. Name the barrier, not argument past it. Doctrinal module waits. Maieutic if a seam of inner recognition is visible. | Double register-hold. Relational register only. | Usually a misread; re-run V1. | Press one specific claim; do not supply argument that will be refused. | Treat as predominantly `juhud` unless genuine inquiry surfaces. |
| `inkar` | Maieutic (P4) + R2. Recognition is present; do not argue. | Identity-performance compounds the denial; pastoral register indefinite hold. | Very rare; re-run V1. | Do not press; `zann-mode` absorbs without landing. | Maieutic wins here more often than argument. |
| `istikbar` | Relational + spiritual. Pride-structure is the barrier. More argument deepens it. | Compound that yields only to long relational investment. Doctrinal modules waste. | Treat as `istikbar`; the autotelic surface is usually a disguise for pride. | Rare. | Relational first in all sub-cases. |
| `nifaq` | Already-believing procedure (P5). Questions requiring inhabited belief. | Common compound; P5 with caution about what the performance is for. | Stop supplying material the performance consumes. | Very common compound; press one specific claim and require it be inhabited. | Re-assess frequently. |
| `mixed` | Name the dominant source-owned pressures and let the stronger present cue govern. | Register-hold until the dominant mode is clearer. | Do not feed the performance; identify which mode is consuming the exchange. | Press one claim only if it clarifies the dominant mode. | Track mode shift explicitly; do not flatten into a loose gloss. |

How to read the matrix:

- The top row is the only row where the full apparatus is deployable without register-shift concerns.
- `clear` means the concealment axis has been positively resolved as non-operative, not left blank.
- Any non-clear concealment + `truth-seek` means the content may be right but the register still governs access. Let the stronger cue govern: one bounded diagnostic question first, then minimal tribunal-clearing only if the blocker stays live, then pause. The matched doctrinal module is held in Layer B, not discarded from Layer A.
- Any concealment + non-`truth-seek` means both axes gate access; the cell names which gate to address first.
- `mixed` DO-orient cells are transitional; track for orientation shift and re-enter the matrix when it stabilizes.

Output: when the register-hold rule applies, include in the case-state line:

```text
Register-hold: <name of the axis gating access>    Deployable on shift to: <what would release the hold>
```

This is consumed by V1's re-run condition and by M5's register-hold field.
