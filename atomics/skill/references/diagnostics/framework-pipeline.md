---
id: framework-pipeline
module_class: governance
canonical_path: skill/references/diagnostics/framework-pipeline.md
contract_version: "0.3.2.0"
load_when:
  - auditing the decision circuit or forbidden-shortcut check
  - surfacing where a response went wrong
  - verifying diagnostic IR gated dispatch rather than documenting it retrospectively
routing_effects:
  - validates pipeline order before render
  - blocks forbidden shortcuts
  - indexes canonical recursive-state governance without owning concrete routing rules
emits:
  - pipeline_integrity_check
  - forbidden_shortcut_check
  - post_render_gate_reference
blocks:
  - retrospective IR formation
  - direct doctrinal rebuttal before diagnostic gate
  - recursive dump after a landed move
  - premature closure without re-entry
companions:
  - diagnostic-ir
  - recursive-state-transitions
  - routing-precedence
  - output-release
  - diagnostic-render-contract
  - anti-patterns
  - P7-restoration-stops
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

# Framework Pipeline - Operative Audit Surface

This file is an operative compiled governance/audit surface. It is not independent
ground truth for every rule it depicts. The source files named at each stage govern
where they conflict with this chart.

Authority boundary:

- This file owns the compact pipeline order and forbidden-shortcut audit surface.
- It owns only semantics explicitly marked here as framework-pipeline semantics.
- `references/diagnostics/recursive-state-transitions.md` owns the abstract
  STOP / HOLD / RECURSE / PARTIAL model and state carry/reset/re-evaluation semantics.
- `references/diagnostics/diagnostic-ir.md` owns typed IR fields, schema carriers,
  and the dispatch gate.
- `references/diagnostics/routing-precedence.md` owns route order, suppression,
  and precedence.
- `references/rubrics/output-release.md` owns release amount, order, and hold/release
  discipline before render.
- `references/rubrics/diagnostic-render-contract.md` owns visible render mode.
- `references/procedures/P7-restoration-stops.md` owns concrete stop instances.

Diagrams, slogans, examples, tradition labels, pattern prints, and background-topic
topics in this file are audit aids. They do not create routes, module activation rules,
IR fields, coverage claims, or source owners.

## Default Final-Output Pipeline Validity

Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It checks
that the proposed default answer actually passed the framework pipeline:

internal diagnosis -> diagnostic reduction -> validated IR -> gate checks ->
routing precedence -> selected live burden -> operative submove(s) -> burden landing ->
output-release rubric -> diagnostic-render-contract -> state re-read -> post-render gate
-> STOP / HOLD / RECURSE / PARTIAL decision

Output-release decides what may be released. Diagnostic-render-contract decides how it
appears. Default final-output preflight checks that the final answer obeys both at the
last mile.

Diagnostic reduction means core axes, mandatory Phase 2 passes, triggered overlays /
specialty markers, Diagnostic IR formation, gate checks, and routing precedence all ran before
the current bounded operator was named. A route chain is not diagnostic reduction.

If a response is clean prose but was produced by topical essay sequencing, it is invalid
and must be rewritten. Clean prose without pipeline validity is still a pipeline failure:
V1 / diagnosis must precede answer; Phase 2 passes must run where triggered; Diagnostic
IR must form internally before routing; routing must come from validated IR; the current
bounded operator must be one selected live-burden function rather than a route chain; TTPs
must be executed as target -> operation -> result inside the selected burden; the burden
must land before state re-read; output-release must run before visible render; the render
contract must shape final prose; state re-read must run after bounded moves; the post-render
gate must run before closure; and STOP / HOLD / RECURSE / PARTIAL must be decided before
ending.

If another eligible same-input live burden remains after the current blocker clears, default
output must either RECURSE into one bounded next pass with a prose state transition, or
mark PARTIAL if limits prevent it. It may not silently STOP.

## Pipeline Audit Chart

<!-- BEGIN GENERATED FRAMEWORK PIPELINE -->
```text
[USER INPUT / CLAIM / EXCERPT]
             |
             v
+--------------------------------------------------+
| ALWAYS-LOAD BACKGROUND                           |
|                                                  |
| terminology.md | case-library/INDEX.md           |
| module-codes.md | heuristics.md                  |
| owner: SKILL.md                                  |
+--------------------------------------------------+
             |
             v
+--------------------------------------------------+
| V1 DIAGNOSTIC GATE                               |
|                                                  |
| diagnosis before answer                          |
| no module before case-state                      |
| listen -> classify -> form IR -> dispatch        |
| owner: techniques/V1-diagnostic.md               |
+--------------------------------------------------+
             |
             v
+--------------------------------------------------+
| PHASE 1: LISTENING                               |
|                                                  |
| map noetic structure                             |
| track anchor / warrant / affective weight        |
| do not answer yet                                |
| owner: diagnostics/noetic-reading-checklist.md   |
+--------------------------------------------------+
             |
             v
+-----------------------------------------------------------+
| DIAGNOSTIC REDUCTION - PHASE 2 AXES + MANDATORY PASSES    |
|                                                           |
| core axes emit case-state features before route selection |
| mandatory passes run inside the diagnostic gate           |
| overlays / specialty markers checked before dispatch      |
| no route itinerary before diagnostic reduction completes  |
| owner: SKILL.md                                           |
|                                                           |
| MANDATORY PASSES - run in sequence:                       |
| [P-A] reason-disambiguation.md                            |
|   emit: reason-category (1-4) + routing gate              |
| [P-B] foreign-premise-detection.md                        |
|   emit: Foreign Premise Detection result                  |
| [P-C] prophetic-discourse-neutralization.md               |
|   emit: semantic-neutralization mode or none active       |
| [P-D] arabic-backbone-predicates.md                       |
|   emit: active predicates or none active                  |
|                                                           |
| Specialty markers surface here only if present.           |
+-----------------------------------------------------------+
             |
             v
+----------------------------------------------------+
| DIAGNOSTIC IR - FORMATION + DISPATCH GATE          |
|                                                    |
| compose IR from Phase 2 outputs                    |
| validated IR is runtime compiler state             |
| IR before routing                                  |
| Pipeline                                           |
| module dispatch blocked until all gate checks pass |
| owner: diagnostics/diagnostic-ir.md                |
+----------------------------------------------------+
             |
             v
       +-----+-----+
       |           |
       v           v
+-----------------------------------------------------------------------+  +----------------------------------------------------+
| GATE BLOCKED                                                          |  | GATE OPEN                                          |
|                                                                       |  |                                                    |
| P7 stops, semantic blockers, or register holds block/compress Layer B |  | gate checks passed; routing precedence may now run |
| Layer A stays live                                                    |  | route cleared for one current live burden          |
| owner: diagnostics/diagnostic-ir.md                                   |  | owner: diagnostics/routing-precedence.md           |
+-----------------------------------------------------------------------+  +----------------------------------------------------+
       |           |
       +-----+-----+
             |
             v
+--------------------------------------------------+
| ROUTING PRECEDENCE                               |
|                                                  |
| levels 1-10 applied after gate checks            |
| upstream blocker before downstream topic         |
| route chain is not bounded operator              |
| TTP entry before activation                      |
| owner: diagnostics/routing-precedence.md         |
+--------------------------------------------------+
             |
             v
+-----------------------------------------------------------------------------------------------------------------------------------+
| SELECTED CURRENT LIVE BURDEN                                                                                                      |
|                                                                                                                                   |
| one live noetic burden/function selected                                                                                          |
| broad enough to contain justified operative submove sequence                                                                      |
| current bounded operator is not a route chain                                                                                     |
| invalid: FPD -> M1 -> DO-8 -> M8 -> restoration                                                                                   |
| invalid split: imported criterion / hujjah / hiddenness as three burden-cycles before same-function or new-burden proof           |
| invalid split: imported tribunal / hiddenness / punishment / named source-worldview as serial burden-cycles without re-read proof |
| not deterministic argument-bank selection                                                                                         |
| owner: rubrics/diagnostic-render-contract.md                                                                                      |
+-----------------------------------------------------------------------------------------------------------------------------------+
             |
             v
+---------------------------------------------------------------------------------------------------------------+
| OPERATIVE SUBMOVE(S)                                                                                          |
|                                                                                                               |
| inside selected live burden only                                                                              |
| entry criteria: validated IR + owner + bounded target                                                         |
| target -> operation -> result                                                                                 |
| ⁿBᵢ[OP] : target -> operation -> result -> ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ                                                |
| derived registers may change state delta / collapse radius when live                                          |
| hujjah/accountability can be operative submove only after same-function proof                                 |
| guidance-as-coercive-proof can be operative submove only after same-function proof                            |
| hiddenness/punishment/source-status can be operative submoves under one burden only after same-function proof |
| distinct input-anchored noetic functions require next burden, HOLD, or PARTIAL                                |
| exit criteria: result + state delta + held-route recheck                                                      |
| operative submoves do not count as recursion                                                                  |
| owner: diagnostics/recursive-state-transitions.md                                                             |
+---------------------------------------------------------------------------------------------------------------+
             |
             v
+------------------------------------------------------------------+
| BURDEN LANDED                                                    |
|                                                                  |
| selected burden lands or remains held                            |
| burden landing precedes state re-read                            |
| Delta-nB remains local; n-plus-1B requires re-read license       |
| state re-read waits for whole burden, not each operative submove |
| depth/stop guards checked before next pass                       |
| restoration/pastoral waits for refresh license                   |
| owner: diagnostics/recursive-state-transitions.md                |
+------------------------------------------------------------------+
             |
             v
+----------------------------------------------------------------+
| OUTPUT GOVERNANCE                                              |
|                                                                |
| default visible Layer A stays compact DSL/IR / fit-for-purpose |
| bounded Layer B only if gate permits                           |
| Layer A / Layer B release checks                               |
| no raw IR / full Case State / matched_modules dump in default  |
| owner: SKILL.md                                                |
+----------------------------------------------------------------+
             |
             v
+-----------------------------------------------------------------------+
| OUTPUT-RELEASE RUBRIC                                                 |
|                                                                       |
| release amount, order, held material, and recursive traversal checked |
| live registers alter release behavior or stay unprinted               |
| output-release before visible response                                |
| owner: rubrics/output-release.md                                      |
+-----------------------------------------------------------------------+
             |
             v
+----------------------------------------------------------------------+
| DIAGNOSTIC RENDER CONTRACT                                           |
|                                                                      |
| Level 1 default compact DSL/IR header plus bounded governed response |
| Level 2 compact DSL / lab-report                                     |
| Level 3 internal/development audit compatibility                     |
| expanded notation is forbidden as decorative proof of execution      |
| diagnostic-render-contract before final shape                        |
| owner: rubrics/diagnostic-render-contract.md                         |
+----------------------------------------------------------------------+
             |
             v
+---------------------------------------------------------------------------+
| LAYER A -> LAYER B -> STATE RE-READ                                       |
|                                                                           |
| one burden-cycle = one live burden -> Layer A -> Layer B -> state re-read |
| one burden-cycle may contain multiple operative submoves                  |
| RECURSE repeats the burden-cycle shape                                    |
| recursion goes through state re-read, not topic transition                |
| multi-burden does not mean multi-recursion by default                     |
| owner: rubrics/diagnostic-render-contract.md                              |
+---------------------------------------------------------------------------+
             |
             v
+-------------------------------------------------------------------+
| POST-RENDER RE-ENTRY GATE                                         |
|                                                                   |
| state re-read asks what cleared and what remains live             |
| held routes rechecked                                             |
| Delta-kappa dependency-radius changes are consumed before closure |
| convergence through controlled state transitions                  |
| decision = STOP / HOLD / RECURSE / PARTIAL                        |
| owner: diagnostics/recursive-state-transitions.md                 |
+-------------------------------------------------------------------+
             |
             v
+--------------------------------------------------+
| RESTORATION TRACE                                |
|                                                  |
| governing misread risk                           |
| what was withheld and why                        |
| correction applied and what remains live         |
| owner: rubrics/diagnostic-render-contract.md     |
+--------------------------------------------------+
             |
             v
+------------------------------------------------------+
| BOTTOM-LINE SYNTHESIS / NEXT MOVE                    |
|                                                      |
| conclusion relative to restored order                |
| one actionable next move                             |
| stop only after the post-render gate permits closure |
| owner: SKILL.md                                      |
+------------------------------------------------------+

RECURSION LOOP
- post_render_gate -> v1_diagnostic_gate [RECURSE through state re-read, not topic transition]
- one bounded live burden per burden-cycle
- burden-cycle begins only after burden landing + state re-read
- depth guard: no next operator without refreshed warrant
- if RECURSE: next input-anchored burden is routed from refreshed state
- STOP only with no eligible burden, or HOLD/PARTIAL reason

PASS SHAPE
- Layer A -> Layer B -> state re-read
- RECURSE repeats the pass shape
- release check: Layer A identifies live burden without route ledger
- release check: Layer B answers only permitted current live burden and operative submoves
- release check: state re-read decides next transition
- release check: topical components remain submoves until re-read licenses a new burden

TTP EXECUTION
- target -> operation -> result -> state re-read
- entry criteria: validated IR exists
- entry criteria: owner-backed selection
- entry criteria: bounded target
- entry criteria: release permission
- exit criteria: result
- exit criteria: state delta
- exit criteria: held-route recheck
- depth guard: no depth increase without burden landing and state re-read
- depth guard: no depth increase for next operative submove under same burden
- depth guard: no depth increase for hiddenness/punishment/source-status when subordinate to same burden
- depth guard: no repeated operator without refreshed warrant
- depth guard: PARTIAL when limits block next eligible burden
- one selected live burden may contain multiple operative submoves
- operative submoves do not count as recursion

GATE CHECKS
1. Mandatory minimum fields populated?
2. Consistency rules pass?
3. routing-precedence.md suppression rules S-1..S-8?
4. P7 stops checked?
5. Architectural integrity check passed?
6. Concealment x orientation matrix permits content now?

TRANSITIONS
- STOP: no eligible live burden remains after state re-read, no held route became eligible, and P7 permits stopping
- HOLD: remaining material exists but its release signal is absent or a hard rail still blocks it
- RECURSE: another same-input live burden remains or a held route becomes newly eligible after the current blocker clears
- PARTIAL: limits prevent completion while recursive pressure remains

EDGE INDEX
- user_input -> always_load
- always_load -> v1_diagnostic_gate
- v1_diagnostic_gate -> phase1_listening
- phase1_listening -> phase2_mandatory_passes
- phase2_mandatory_passes -> diagnostic_ir
- diagnostic_ir -> gate_blocked
- diagnostic_ir -> gate_open
- gate_blocked -> output_governance
- gate_open -> routing_precedence
- routing_precedence -> selected_live_burden
- selected_live_burden -> operative_submoves
- operative_submoves -> burden_result
- burden_result -> output_governance
- output_governance -> output_release
- output_release -> render_contract
- render_contract -> pass_shape
- pass_shape -> post_render_gate
- post_render_gate -> restoration_trace
- restoration_trace -> bottom_line
- post_render_gate -> v1_diagnostic_gate [RECURSE through state re-read, not topic transition]

FORBIDDEN SHORTCUTS (generated index)
- [INPUT] -> [direct doctrinal rebuttal]
- [philosophical vocabulary appears] -> [auto-load sound-reason-epistemology.md]
- [grief / wound / identity-perf] -> [argument / theodicy / doctrinal counter]
- [thin basis / one sentence] -> [confident motive read or family lock]
- [RT pressure appears] -> [broad doctrinal rebuttal first]
- [landed move] -> [stack next argument immediately]
- [IR formed retrospectively] -> [counts as gate pass]
- [usurpation visible] -> [defend revelation within usurping framework]
- [backbone predicate trigger present] -> [none active emitted without checking]
- [semantic neutralization / loaded anti-attribute term] -> [release doctrinal content anyway]
- [downstream content detected] -> [held but never reassessed after blocker clears]
- [held = wait for user reply] -> [no same-response recursion ever]
- [recursive traversal permitted] -> [argument dump at one refresh]
- [same-response recursion] -> [Move 1 / Move 2 / Move 3 essay ladder]
- [route itinerary formed before diagnostic reduction] -> [current bounded operator]
- [Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration] -> [valid live burden]
- [Burden-1 operative submoves] -> [Pass 1 / Pass 2 / Pass 3 recursion]
- [imported tribunal / hiddenness / punishment / named source-worldview topical components] -> [serial burden-cycles without state/noetic re-read proof]
- [TTP named in prose] -> [TTP treated as executed]
- [topic cue] -> [deterministic argument bank]
- [TTP route itinerary] -> [recursion without entry / exit criteria]
- [Layer A held route] -> [Layer B answers held content]
- [recursive depth] -> [prose momentum without state re-read]
- [restoration / pastoral note] -> [before state re-read]
- [bounded move rendered] -> [STOP without post-render gate]
- [diagnostic transparency allowed] -> [machinery dump]
- [default response complete] -> [bibliography / source dump]
- [background topic appears] -> [argument bank / citation dump]
- [tradition label appears] -> [tradition-specific answer]
- [pattern print emitted] -> [PF / routing precedence bypassed]
- [Ashʿarī / Māturīdī / Atharī / Taymiyyan / kalāmic / falsafah cited together] -> [one unified operative authority]
- [classical theology / classical tradition / mainstream kalam] -> [peer-valid operative support across contradictory schools]
- [source marked contrast / opponent-position / historical note / held] -> [operative warrant in the same burden-cycle without reclassification]
- [school-sensitive claim] -> [Ashʿarī / Māturīdī teaches X as settled]
- [agreement asserted across frames] -> [operative support without substantive vs. verbal marking]
- [state re-read / noetic re-read block printed] -> [burden landed asserted without preceding operative submove result]
- [still live entry in re-read block] -> [material not present in input / held / preceding collapse radius]
- [next licensed live burden] -> [not anchored in still live / held / original input]
- [re-read block alone] -> [new burden-cycle without prior burden result]

CONCEPT OWNERSHIP (owner-backed)
- IR formation: diagnostics/diagnostic-ir.md
- routing: diagnostics/routing-precedence.md
- selected current live burden: rubrics/diagnostic-render-contract.md
- render shape: rubrics/diagnostic-render-contract.md
- output release: rubrics/output-release.md
- recursion: diagnostics/recursive-state-transitions.md
- framework-pipeline audit surface: diagnostics/framework-pipeline.md
- DSL/IR representation: diagnostics/diagnostic-ir.md
- meta-noetic memetics object-domain: diagnostics/diagnostic-ir.md
- Pipeline: diagnostics/diagnostic-ir.md
- runtime diagnostic compiler contract: diagnostics/diagnostic-ir.md
- TTP entry / exit criteria: diagnostics/recursive-state-transitions.md
- Layer A / Layer B release checks: rubrics/output-release.md
- source-status & noetic-frame non-equivalence: diagnostics/recursive-state-transitions.md
- grounded noetic re-read shape: diagnostics/recursive-state-transitions.md

REQUIRED ORDER
- user_input -> always_load -> v1_diagnostic_gate -> phase1_listening -> phase2_mandatory_passes -> diagnostic_ir -> gate_blocked -> gate_open -> routing_precedence -> selected_live_burden -> operative_submoves -> burden_result -> output_governance -> output_release -> render_contract -> pass_shape -> post_render_gate -> restoration_trace -> bottom_line
```
<!-- END GENERATED FRAMEWORK PIPELINE -->


## Compact Pipeline Order

`diagnostic reduction -> IR -> gate checks -> routing precedence -> selected live burden -> operative submove(s) -> burden landing -> output-release -> render contract -> bounded output -> state re-read -> recursive-state-transitions decision`

## Selective Deployment Branch

Certain slogan families require a selective deployment branch inside the same mandatory-pass
architecture, especially PF-2 / P6 worldview-deflection and pseudo-neutrality cases:
"I have no religion," "I just follow the evidence," "I'm neutral," "I'm just following
reason," or "I looked and just wasn't convinced" when the slogan is functioning as an
already-installed tribunal rather than a formed inquiry.

Run the full Phase 2 stack and form the full IR exactly as usual. Then, if the case-state
shows reason-category 3 or 4 together with foreign premise / tribunal installation and a
live concealment or register-control read, retain the full diagnosis internally for
audit-capable render modes while compressing Layer B to one bounded question or minimal
tribunal-clearing. Default visible
Layer A remains fit-for-purpose and bounded by `diagnostic-render-contract.md`; it does not
become a whole-diagnosis dump. This branch exists to preserve memetic precision and avoid
rewarding deflection with over-disclosure; it is not a shortcut around the diagnostic gate.

## Forbidden Shortcut Paths

- `[INPUT] -> [direct doctrinal rebuttal]`
  Bypasses V1 and the diagnostic IR gate entirely.
- `[philosophical vocabulary appears] -> [auto-load sound-reason-epistemology.md]`
  Turns non-default substrate into ambient default.
- `[grief / wound / identity-perf] -> [argument / theodicy / doctrinal counter]`
  Violates P7 Stop-1 and the concealment x orientation matrix.
- `[thin basis / one sentence] -> [confident motive read or family lock]`
  Violates underdetermined discipline and Stop-4.
- `[RT pressure appears] -> [broad doctrinal rebuttal first]`
  Skips V10 transmission vetting and the FPD pass.
- `[landed move] -> [stack next argument immediately]`
  Violates Stop-2 and recursive-state boundary reset.
- `[IR formed retrospectively] -> [counts as gate pass]`
  IR written after dispatch is cosmetic compliance.
- `[usurpation visible] -> [defend revelation within usurping framework]`
  Grants tribunal jurisdiction.
- `[backbone predicate trigger present] -> ["none active" emitted without checking]`
  Uses the compression rule as a bypass.
- `[semantic neutralization / loaded anti-attribute term] -> [release doctrinal content anyway]`
  Bypasses the `semantic-discipline-required` gate; clear recontenting, evacuation, or the lexical trap first.
- `[downstream content detected] -> [held but never reassessed after blocker clears]`
  Treats held as permanent suppression rather than traversal-delayed.
- `[held = wait for user reply] -> [no same-response recursion ever]`
  State re-read is an internal operation; it may occur inside the same response.
- `[recursive traversal permitted] -> [argument dump at one refresh]`
  Recursion is burden-cycle by burden-cycle, not total-downstream release at one state re-read.
- `[same-response recursion] -> ["Move 1 / Move 2 / Move 3" essay ladder]`
  Numbered essay sequencing is not state re-read. RECURSE requires a prose state
  transition naming what cleared, what remains live, why the next burden was already
  present, and why the next bounded pass is eligible.
- `[route itinerary formed before diagnostic reduction] -> [current bounded operator]`
  Diagnostic reduction must complete before routing. A route itinerary formed early is a
  bypass of axes, mandatory passes, IR formation, gate checks, and routing precedence.
- `[Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration] -> [valid live burden]`
  The current bounded operator is one selected live-burden function, not a module itinerary.
- `[Burden-1 operative submoves] -> ["Pass 1 / Pass 2 / Pass 3" recursion]`
  Operative submoves under the same burden are not burden-cycles. Recursion begins only
  after burden landing and state re-read license the next input-anchored burden.
- `[imported tribunal / hiddenness / punishment / named source-worldview topical components] -> [serial burden-cycles without state/noetic re-read proof]`
  Same-cluster facets stay inside one live burden as operative submoves unless `R` licenses
  a genuinely new input-anchored burden.
- `[TTP named in prose] -> [TTP treated as executed]`
  TTP activation is selected by validated IR and performed as a bounded operation. A
  phrase such as "the M1 move" or "the M8 move" is not source-backed execution by itself.
- `[topic cue] -> [deterministic argument bank]`
  The skill is a runtime-verifiable diagnostic compiler, not a deterministic answer
  selector. Topic recognition does not replace diagnostic reduction, validated IR, and
  operator activation.
- `[TTP route itinerary] -> [recursion without entry / exit criteria]`
  TTP recursion requires entry criteria, operation criteria, exit criteria, and refreshed
  state selection at each depth. An initial itinerary cannot license downstream operators.
- `[Layer A held route] -> [Layer B answers held content]`
  Layer A may name held routes for auditability; Layer B may not answer them until state
  re-read licenses release.
- `[recursive depth] -> [prose momentum without state re-read]`
  Depth increases only after burden landing and state re-read. Continuing because another
  topic is nearby, or stopping because the first argument landed, violates convergence.
- `[restoration / pastoral note] -> [before state re-read]`
  Restoration synthesis and pastoral note wait until the active burden lands and state re-read
  licenses closure, HOLD, PARTIAL, or the next live burden.
- `[bounded move rendered] -> [STOP without post-render gate]`
  Premature closure. The state re-read / re-entry gate must recheck held routes before STOP.
- `[diagnostic transparency allowed] -> [machinery dump]`
  Diagnostic render eligibility does not suspend output-release rubric.
- `[default response complete] -> [bibliography / source dump]`
  Default mode suppresses source-basis ledgers and bibliography/source-list endings unless
  the user requested sources or the task is audit/research.
- `[background topic appears] -> [argument bank / citation dump]`
  Background material supplies structural framing only. It does not bypass IR formation, source-use discipline, owner selection, or release limits.
- `[tradition label appears] -> [tradition-specific answer]`
  "Jewish", "Hindu", "Sufi", or "Buddhist" is not itself a route. Type the load-bearing node first: authority order, criterion, semantic hinge, category-set, identity wound, or transmission layer.
- `[pattern print emitted] -> [PF / routing precedence bypassed]`
  Structural pattern print is an optional IR descriptor, not a new V-pass, PF replacement, or coverage claim.
- `[Ashʿarī / Māturīdī / Atharī / Taymiyyan / kalāmic / falsafah cited together] -> [one unified operative authority]`
  Contradictory noetic structures cannot be released as one operative authority. Each
  burden-cycle proceeds from one selected operative noetic frame; other frames may be
  named only under non-operative source-status.
- `[classical theology / classical tradition / mainstream kalam] -> [peer-valid operative support across contradictory schools]`
  Umbrella terms that flatten contradictory schools are forbidden when the claim is
  school-sensitive or disputed. Identify the selected operative frame.
- `[source marked contrast / opponent-position / historical note / held] -> [operative warrant in the same burden-cycle without reclassification]`
  A source carrying a non-operative status must not become operative warrant without an
  explicit reclassification sentence naming the reason and preserving the selected frame.
- `[school-sensitive claim] -> [Ashʿarī / Māturīdī teaches X as settled]`
  Intra-school flattening hides internal disagreement. Mark school-sensitive claims as
  disputed or use them only under contrast / historical-note status.
- `[agreement asserted across frames] -> [operative support without substantive vs. verbal marking]`
  Verbal-only agreement across frames is not operative support. If agreement is asserted,
  mark whether it is substantive or merely verbal/surface-level.
- `[state re-read / noetic re-read block printed] -> [burden landed asserted without preceding operative submove result]`
  The re-read block must be grounded in an immediately preceding operative submove with
  `target -> operation -> result`.
- `[still live entry in re-read block] -> [material not present in input / held / preceding collapse radius]`
  `still live` must be anchored in the original input, prior held material, or the
  preceding burden-cycle's collapse radius.
- `[next licensed live burden] -> [not anchored in still live / held / original input]`
  A new burden cannot be invented at the re-read step.
- `[re-read block alone] -> [new burden-cycle without prior burden result]`
  A new burden-cycle requires a grounded re-read whose `burden landed` traces to a real
  operative result.

## Recursive State-Transition Reference

The abstract recursive state-transition model is owned by
`references/diagnostics/recursive-state-transitions.md`. This pipeline chart must show the
post-render re-entry position, but it does not independently define STOP, HOLD, RECURSE,
PARTIAL, state carry/reset/re-evaluation, or same-response recursion conditions.

The post-render gate is the circuit position. `recursive-state-transitions.md` is the abstract
semantic owner. `diagnostic-ir.md` is the typed carrier. `output-release.md` governs release
amount/order. `diagnostic-render-contract.md` governs visible render mode. `routing-precedence.md`
governs route order and suppression. `P7-restoration-stops.md` owns concrete stop instances.

## Noetic / Meta-Noetic Vocabulary Scope

Noetic structure is the object of diagnosis. It is the operative configuration by which a subject
judges reality: commitments, categories, inferential norms, testimonial attitudes, interpretive
filters, background assumptions, and belief-relations.

Meta-noetic memetics describes how whole noetic structures and their governing epistemic rules
form, function, stabilize, defend themselves, mutate, reproduce, spread, and instantiate
linguistically across persons and communities. It asks how a structure treats things as basic,
obvious, rational, neutral, evidential, authoritative, or interpretable; how its beliefs support
each other; which social and linguistic patterns reproduce it; and what load-bearing node keeps
regenerating the same downstream claims.

DSL/IR operationalizes these readings through existing fields and owners. This vocabulary does
not create a new routing pass, does not create new IR fields by itself, and does not override
`noetic-reading-checklist.md`, `diagnostic-ir.md`, `pattern-profiling.md`, or
`routing-precedence.md`. Examples, slogans, tradition labels, and pattern prints do not create
routes.

## Compiled Runtime Note

In the compiled runtime, atomized paths named in this pipeline are source identities. They do
not require the standalone atomized file to exist under the generated runtime root. Resolve the
original module ID or source path through `compiled-module-map.json`, load the containing runtime
bundle or omnibus file, and use only the section with the matching `MODULE_ID`. Matched modules
remain original module IDs; omnibus filenames are containers, not active dispatch.

## Formalization Pointer

The former formal operator notation, Mermaid graph, symbol legends, functional pipeline
explanation, and interpretive conclusion live in `docs/audits/framework-pipeline-formalization.md`.
That document is explanatory / audit formalization only. It is not live routing authority and
does not create routes, module activation rules, IR fields, or source owners.

## Coverage Verification

- Failure condition: Any direct jump from user input to doctrinal rebuttal, retrospective IR formation after dispatch, or recursive dump after a landed move violates the pipeline.
- IR-visible consequence: The validated IR must precede owner activation, output release, render selection, and refreshed-state continuation.
- Minimal pair: A governed same-response recursion follows a landed move plus refresh plus renewed permission; an argument stack is merely accumulated downstream content without refreshed governance.
- Hold/release rule: The gate-blocked branch keeps Layer A live and compresses or withholds Layer B until stops, semantic blockers, or register holds clear.
- Anti-pattern guard: Do not treat the ASCII chart as a decorative report; it is an audit surface for whether the runtime dispatch order was obeyed.
