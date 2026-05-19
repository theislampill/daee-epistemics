---
id: output-release
module_class: governance
canonical_path: skill/references/rubrics/output-release.md
contract_version: "0.4.0.0"
load_when:
  - any response about to be shaped or released
routing_effects:
  - governs how much may be released, in what order, and under what case-state conditions
catalogue_registered: false
---

# Output-Release Rubric

PACK-SPEC note: this file functions as a release contract owner. For future normative edits, use
`docs/spec-authoring-pack.md`; keep uppercase MUST / SHOULD / MAY intentional and backed by
examples or checks.

## Function

This runtime governance rubric runs after dispatch and before final public render. It decides
release amount/order, held/released discipline, compact render eligibility, same-response
recursion, and why STOP, HOLD, RECURSE, or PARTIAL is the closure state. It is not a topic
bank, argument bank, or mandate to expose all internal diagnostic fields.

## Pipeline Position

```
raw discourse
-> diagnostic reduction: core axes + mandatory Phase 2 passes + overlays / specialty markers
→ noetic / memetic pressure read
→ typed IR
-> gate checks
-> routing precedence
→ ∇ route-gradient over eligible live pressure
-> selected current live burden
→ PF atom(s) / claim-level overlay
→ canonical owner(s)
-> internal TTP step(s): target -> operation -> result
-> burden landing
→ ΔⁿB / Δκ event-local transition
→ target-explicit ∇· / ∇× field diagnostics
→ LoopBreak(∇×T) if a licensed loop-breaker is required
→ family-local load floor
→ output-release rubric        ← THIS FILE
→ diagnostic render contract
→ bounded public response
→ post-render state re-read / re-entry gate
→ closure-field condition 𝒞(Ψᴺ)
→ STOP / HOLD / RECURSE / PARTIAL
→ next governed pass if eligible
```

**Division of labour:**
- Routing decides what is eligible.
- Canonical owners decide what must be addressed.
- Family-local load floor decides what must be loaded.
- Output-release rubric decides what may be released now.
- Diagnostic render contract decides how visibly structured the output is.
- Post-render gate reassesses what remains live, drops, compresses, or becomes eligible.
- P7 stop discipline constrains the gate's STOP, HOLD, RECURSE, or PARTIAL decision.

Do not collapse these into one step. Do not let visible render shape determine routing.

---

## Scope Guard

This rubric governs release order and re-entry. It is not a render template, routing engine,
proof bank, or permission to dump held downstream material.

**Core principle:** use the runtime notation owned by `recursive-state-transitions.md`:
`H(n+1) = (Hn ∪ InputLive_n) - Released_n`; `Land(B) -> R`; `R required before STOP/RECURSE`.
Gloss: Held means traversal-delayed, not response-delayed. Apply the governing TTP, refresh
state, reassess upstream/downstream and first-/higher-order burdens, then continue only if another
permitted `B` remains live. STOP is invalid unless the post-render gate has run; if another live
distortion or newly eligible held route remains, choose RECURSE, HOLD, or PARTIAL as governed.
No premature STOP: do not close while an eligible live burden remains.

Plain `∇` is the route-gradient read over eligible live pressure before the selected burden is
released. In default render it prints only as part of Layer A's gate/release decision, before
Layer B releases the burden: `∇ route: Bn pressure highest — [dependency-reduction reason] over
[held alternatives]`. It explains why the selected burden has the highest expected diagnostic
reduction, closure yield, or dependency-clarification yield among currently eligible routes. It
remains constrained by Diagnostic IR, V1/routing precedence, owner catalogue eligibility, and
held-material discipline. It does not bypass gates, prove truth/warrant, replace `Δ`, or turn
multiple live candidate structures into one deterministic route. Its formal role is
route-ranking/preorder pressure, not literal vector gradient.

> Render surface does not change governance. Default `/daee-epistemics` is the canonical compact DSL-governed surface: readable, bounded, and visibly carrying a mandatory noetic-field execution banner, compact DSL/IR header, governed Layer B, and state/noetic re-read. It is not prose-only mode. `/daee-epistemics:dsl` exposes expanded Diagnostic IR / live-burden state; it is not the first place DSL governance appears. `/daee-epistemics < input.md > output.md` is canonical file-retained execution: the same compact DSL-governed surface is written to `output.md` when final-chat delivery would compress a hard answer. `/daee-epistemics:audit` is deprecated as a public render mode and retained only for internal/development audit compatibility. The former external recursive-audit prompt is deprecated as normal prompting because its useful discipline is now native.

**Same-response RECURSE trigger checklist:**
After every bounded move, `Land(B) -> R` decides whether recursion is active now:
1. Current blocker cleared enough to release the next live burden.
2. Another already-present burden remains live in the original input.
3. No P7 stop, register-hold, semantic gate, thin-basis rule, absent release signal, or limit blocks the next pass.

When all three are true, `RECURSE` is required internally in the same response. Do not convert this into an audit ledger in default mode; continue through the next bounded prose section. If the burden remains live but an absent release signal blocks it, hold in prose. If limits prevent the next eligible pass, render partial release-status prose. `STOP` remains the internal decision that is invalid while this checklist is satisfied. This same-response recursion requirement is a scriptless compact-DSL obligation, not merely optional script-harness route behavior.

Derived register release discipline: when a response uses the expanded formalism from
`docs/algebraic-notation-and-noetic-formalism.md`, each live register must change release
behavior rather than decorate the prose. `♥` may affect hold, sequence, softness, directness,
or closure posture; `ξ` may affect proof/warrant/testimony release; `Ω` may affect predicate,
category, modality, or dependence release; `μ` may affect carrier/stabilizer handling; `κ` /
`Δκ` may affect downstream reread. If none of these changes the governed burden, owner, held
material, `Land(B)`, or `R(H,Δ)`, do not print the symbol. `κ` is not a TODO list, and
`ΔⁿB` is not a shortcut to a new burden-cycle.

Default governed render is not compact in the sense of hiding governance. It must surface a
compact witness wherever a field operator controls release, recursion, hold, partial, or closure.
Layer A prints `∇ route: ...` in the gate/release decision whenever eligible burden ordering,
held alternatives, or dependency pressure selects one burden over another. After every `Land(B)`,
`R(H,Δ)` prints a target-explicit field-diagnostic witness:
`∇·<target>: <positive|bounded|neutral|null>; ∇×<target>: <nonzero|resolved|held|null>`.
Null checks are visible when they license RECURSE, PARTIAL, or COMPLETE; they are suppressed only
when no burden has landed or no explicit field target/control effect exists. In hard or
multi-burden default output, a bare `R(H,Δ)` / `R(H,Delta)` continuation line is invalid unless
the same state re-read also prints literal `Field diagnostics:` and `LoopBreak:` witness lines.
`LoopBreak:` prints `not needed` when `∇×` is null, or the licensed target loop, grounding source,
burden/submove, `Δ` effect, and post-break reread when nonzero. Use `R(H,Δ)` as the
formal notation and `R(H,Delta)` only as the ASCII fallback. The expanded formal reread is
`R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)`; the expanded ASCII fallback is
`R(H, Delta-nB{heart,xi,Omega,sigma,mu}, Delta-kappa)`. If the reread itself is the pressure
point, use `TTP-MRP-mid-reread-pressure` to activate existing pressure owners/classes and record
whether their outputs license genuine dependency, partial real burden, hidden-framework recoil,
label-pressure, doubt-churn, reorientation/reminder, or stable no-new-burden closure before
release. MRP licenses graph deltas for RECURSE/HOLD, blocks proof-stacking when LoopBreak or STOP
is the governed route, and makes `∇·T` / `∇×T` active reread gates rather than final labels. `∇·` and `∇×` remain forbidden as
decorative proof of execution: they must have an explicit field target and be tied to the
noetic/burden/dependency/register/route field, `κ/H`, dependency pressure, loop-breaking,
`R(H,Δ)`, PARTIAL, RECURSE, COMPLETE, or checker outcome. They may render as `∇·κ` / `∇×κ`
when `κ` is the diagnostic target, but they are not restricted to `κ`. Allowed default:
`State: Δκ live; ∇·κ positive; ∇×κ unresolved; R(H,Δ): RECURSE.` `Burden field: ΔⁿB landed;
∇·B positive over B3/B4; ∇×B unresolved around compact-neutrality dependency.` `Register
field: ∇·♥ positive; ∇×ξ unresolved; R(H,Δ): HOLD.` Forbidden default: `The antisymmetric
Jacobian of the noetic field shows...`; `The ∇× symbol proves the TTP executed.`
`del-dot` and `del-cross` are ASCII aliases for `∇·` and `∇×`, not separate operators; if
Unicode is unavailable they may appear only as compact, target-explicit state markers with the
same control-effect boundary.

If compact `∇×T` remains nonzero, the release decision must account for loop-breaking eligibility.
`LoopBreak(∇×T)` may be released only when the output identifies the target loop, an
owner-licensed grounding source, the burden/submove that breaks the loop, the resulting `Δ`
effect, and a post-break `∇×T` reread. If no loop-breaker is licensed, the loop is held with
reason or carried into RECURSE/PARTIAL rather than hidden behind closure prose. It is a partial
licensed transition, not a total transition.

LoopBreak is conditional and control-bound. Do not require a decorative `LoopBreak:` line in every
ordinary output. When field diagnostics are rendered and cyclic pressure was checked, null cyclic
pressure must render as `LoopBreak: not needed` / `not licensed` / equivalent; non-null cyclic
pressure must name target, ground, `Δ` effect, post-break reread, and resulting hold/closure
state.

General noetic-selection / register-control release guard: Prompt brevity does not imply simple execution and is not a release permission. Every `/daee-epistemics` release surface, including clarifying or missing-input
replies, begins with the noetic-field execution banner as first visible content. The first visible
surface must visibly signal governed execution with `NOETIC FIELD EXECUTION` and the banner fields;
do not reduce success to a bare `field:` line, prose, headings, apologies, Markdown fences, banner
summaries, or clarifying questions before it, and do not wrap the banner in a code block.
If a source-authentication case is missing the actual
report/text/reference, mark the banner as `SOURCE-AUTHENTICATION`, `user task:
SOURCE-AUTHENTICATION`, `external source request: IMPLICIT`, authority frame `LIVE`, state
`PARTIAL`, then ask for the missing material. For `/daee-epistemics refute:` or similar task
verbs, mark the user task explicitly (for example `REFUTE`) even when `external source request`
is `NONE EXPLICIT`.

Noetic structures, burdens, submoves, dependencies, registers, routes, and closure pressures
must not be treated as scalar summaries. They are relational field states in token/noetic space:
they can carry directed dependency, residual outward pressure, circularity, overlap, conflict,
and unresolved route pressure. For that reason, `Δ` and `∇·` / `∇×` notation is not
ornamental. `Δ` marks event-local transition over a burden or field state. `∇·` reads
divergence-like residual outward pressure in an explicit target field. `∇×` reads
curl-like circularity, rotational dependency, or unresolved cyclic pressure in an explicit target
field. These operators do not apply to a scalarized master diagnosis. They apply only after the
runtime has preserved a live noetic/burden/dependency/register/route/collapse field with explicit
target and control effect. `κ` is the collapse/closure-state target when rendered as `∇·κ` or
`∇×κ`, but the operators are not restricted to `κ`. Scalar collapse is an execution failure
because divergence and curl are field diagnostics, and fields are lost when the noetic structure
is reduced to a one-point summary.

When a hard case admits multiple valid noetic-structure selections, the selected execution path
is the release order over the live noetic field, not the whole field itself. The runtime must
construct and govern a burden/dependency/register/route field containing valid candidate
structures, burdens, submoves, overlaps, dependencies, conflicts, and residual pressures. After
each landed burden, `R(H,Delta)` must reread the entire live field, not only the last selected
route. Remaining first-order and higher-order operations, alternate valid structures, hidden
dependencies, circularities, and residual pressures must be addressed, integrated, discharged as
duplicate/derivative, explicitly held with reason, or carried forward into RECURSE. TTP coverage
is eligibility-aware: check live pressure against available owner/TTP space, but do not force
every TTP onto every burden regardless of fit.
The final restorative response must preserve the master deformation discovered during execution.
If the governed read discovers that an input is functioning as a power-map rather than a truth
rebuttal, closing prose must not drop that diagnosis merely because another valid route was
selected first.

For any input `D0`, `R(H,Delta)` must inspect selected/held noetic frames, live heart, xi,
Omega, sigma, mu, kappa, held-burden dependencies, and residual field pressure before final
restoration. It may not STOP or mark COMPLETE while downstream dependencies remain. Render,
clear, integrate, discharge as duplicate/derivative, hold with reason, or mark PARTIAL/RECURSE.
Bare-symbol reread is invalid: the state/noetic re-read must recover held set, live remainder,
newly released or newly blocked routes, and next eligible pass / STOP-HOLD-PARTIAL-RECURSE-
COMPLETE status, or a compact equivalent.

Closure/reconstruction must distinguish three surfaces: the burden dependency graph, the coverage
proof, and the collapse/closure proof. `R(H,Δ)` rereads the updated state and must account for the
initial burden set through terminal states or explicit carry/hold decisions. A parseable graph
alone is not enough: every initial burden must have exactly one terminal accounting line, and
COMPLETE / positive closure is not licensed unless residual `∇·B` is neutral and `∇×κ` is null or
resolved for the scoped field.
The initial burden set must be declared from Layer A / Diagnostic IR before release accounting; it
is not discovered retroactively by the closure witness. If `R(H,Δ)` exposes a burden not in that
pre-release set, render it as newly discovered, newly live, or a next-pass candidate, then HOLD,
PARTIAL, or RECURSE unless the scoped closure rule explicitly permits current-pass terminal
accounting without pretending the original set was complete.

If the answer closes a multi-burden, register-active, named-worldview, source-authentication,
mixed noetic-field, or authority-frame case, the closure audit must visibly account for
candidate/held `N` frames, selected primary `N`, live registers, active or cleared owner/TTP
child modes, `Delta-nB`, `Delta-kappa`, target-explicit `∇·` / `∇×` results, and remaining
kappa / H status. Case-shaped dependencies appear only where live. The compact dependency graph
uses parseable edge notation: `(root)` marks no upstream dependency, `A → B` means B depends on A
landing first, and `A ∥ B` means A and B are parallel / independent at that level. Example:
`B1 (root); B1 → B2; B1 → B3; B2 ∥ B3`. If that accounting cannot be rendered, mark PARTIAL or
RECURSE instead of COMPLETE.
The visible default section heading for this final accounting is literal
`Closure/Reconstruction Witness`; do not replace it with `Closure audit` or collapse
`Burden dependency graph:` into a shorter `burden graph` label.

Terminal release boundary: `𝒞(Ψᴺ)` and `N_fiṭrī ∧ ʿaql ṣarīḥ` may be named only after the
burden-state delta has landed and reread has decided there is no unhandled live distortion
requiring another pass. In default render, `𝒞(Ψᴺ)` appears as a compact closure marker when
COMPLETE/STOP is licensed, because closure is a positive field configuration, not checklist
exhaustion. It never licenses a restoration paragraph before owner/TTP execution, visible closure
audit, P1/P7 closure, and live M1/M1-P or M9 obligations have been satisfied or held/PARTIALed.

Positive closure-field condition: `𝒞(Ψᴺ)` means the agent execution field has reached a governed
release configuration, not that a checklist is empty and not that the interlocutor has accepted
truth. STOP requires landed/integrated/held burdens, neutral or bounded residual `∇·` pressure,
resolved or explicitly held `∇×` loops, recoverable route reconstruction, and no hidden live
pressure requiring RECURSE/PARTIAL.

The visible closure block must identify whether the agent execution field is COMPLETE, STOP, HOLD,
PARTIAL, or RECURSE. `𝒞(Ψᴺ)` remains runtime-side closure only and never indicates interlocutor
acceptance, conversion, persuasion, guidance, or soul access.

Agent/interlocutor field boundary: the runtime operates in `Ψᴺ`, the agent execution field. It
diagnoses an interlocutor field `Ψᴵ` only through discourse/profile/register/source-status
evidence and releases through language-mediated coupling `T_lang: Ψᴺ ⇢ Ψᴵ`. Final restorative
boundary text must articulate this compactly when closure or final counsel is rendered: the
released response is a language-mediated coupling attempt from the governed agent field toward the
diagnosed interlocutor field. This is a partial coupling relation, not an isomorphism, not a
surjection, and not a guaranteed update operator on `Ψᴵ`. Output may assess whether the coupling attempt is
identity-preserving and non-deformative; it must not claim access to the interlocutor's soul,
guaranteed uptake, or agent control of guidance.

Release-smoke witness capture mode is a local package-bound evidence mode. It does not change what
may be released, but it makes release decisions and closure boundaries literal: `∇ route`,
`Field diagnostics:`, `LoopBreak:`, `R(H,Delta)`, `Closure/Reconstruction Witness`,
`𝒞(Ψᴺ)`, `T_lang: Ψᴺ ⇢ Ψᴵ`, `Restorative Response`, and `Closing Formulation` must be
checker-readable when the manifest says `witness_required=true`. Missing surfaces are not
silently downgraded to "not applicable"; non-applicability must be declared by case type before
capture. Witness markers remain evidence surfaces, not competence proof, not a truth meter, and
not guaranteed uptake.

For file-retained execution, the same release decision governs the file, not the final chat
message. Write the complete, HOLD, or PARTIAL governed answer to the output file. The chat
response reports only status, path, and approximate length; it must not become a shorter
replacement for the governed answer. File-retained execution must not run repo checkers, route
tools, smoke-artifact tools, or execution-fidelity checks unless the user explicitly requests
developer validation; do not add harness verdicts, `execution_fidelity`, route-plan claims, or
source-audit commentary to the status report. Do not add source links, sanity scans, checker
notes, or extra commentary. For hard or multi-burden file-retained answers, keep explicit
`Land(Bn)` and `R(H,Delta)` attachment per released burden; do not replace them with a generic
state paragraph.

**Minimum visible transition spine (mandatory in multi-burden default):**
`B -> {s1...sn} -> Land(B) -> R -> Decision`. Gloss: a live burden is input-anchored
noetic state, not topic count; topic transition != recursion; component tour != recursion.
State re-read enumeration of remaining input-anchored live burdens plus one newly routed bounded
pass = recursion.
For hard, compound, or deformed recursive cases, the next bounded pass begins with a fresh
compact Layer A for that burden before Layer B resumes. Layer A is the live diagnostic control
state; Layer B is the governed intervention. This keeps continuation from becoming a checklist
or route queue without renewed noetic assessment.
Layer A diagnoses and licenses; it does not argue, become a proof-chain, or create a further
burden. Layer B operates and releases; it performs the active TTP/operator submoves needed to
land the current burden and does not automatically create new burdens. `Land(B) -> R(H,Delta)`
is the principled stop/continue/hold/partial gate that prevents regress, arbitrary stopping,
Layer A overgrowth, and Layer B flattening.
That gate is ordered by noetic structure: first-order surface claim, second-order criterion/
warrant/proof-method/source-authority/testimony standard/moral tribunal, and higher-order or
meta-noetic source-worldview/register/source-status/noetic-frame pressure. Recurse when a
distinct order remains live after landing; do not recurse because more content is available,
and do not collapse distinct orders into one omnibus burden.
This ordering protects noetic function, reliable warrant-process, and foundational order:
what is being treated as basic, what is inferred, which hidden premise or source-rule is acting
as foundation, and whether the claim-assessing process is truth-conducive or deformed by an
imported tribunal, selective testimony rule, scientistic filter, anti-revelation prior, grief/
identity pressure, source inversion, or desire.
`R(H,Delta)` must judge the refreshed state: continue, hold/defer, skip as no longer live,
mark PARTIAL, request bounded reroute when the live state materially changed, or close when
no input-anchored burden remains. A planned continuation queue proposes order; it does not
override this state-transition judgment.

For the required compact DSL/IR header + Layer B + State/noetic re-read shape, Layer A limits, and
single-pass Layer A/B surface-compliance failure guard, use `diagnostic-render-contract.md`. For the
minimum visible transition spine and valid transition example, use
`recursive-state-transitions.md`.

For moral-protest / hiddenness / imported-criterion cases, the transition should show this
behavioral shape: the imported criterion is concretely identified; criterion test is actually performed; result changes case-state; remaining same-input live burden is named or held with condition; and, if recursion occurs, prose transition plus bounded next pass appears.
Do not treat personal identity labels as proof of motive, and do not release
hiddenness, hell, accountability, consequence tracing, mercy, pastoral material, and sources as
a single default-mode essay sequence.
Drift guard: mandatory default compact DSL/IR header; no named-example route; no default raw IR/Case State/route ledger.

TTP activation is not naming a move in prose. A valid TTP pass requires that the TTP be
selected by validated case-state / IR, assigned a bounded target, and used to perform its
specific operation. The output must reflect that operation; it must not merely call a
paragraph "the M1 move" or "the M8 move." Downstream TTPs are released only after state
re-read makes them the next eligible pass.

The specific operation is owner-specific. A generic Target/Operation/Result line does not
release a TTP unless the operation satisfies the owner-specific operation floor in the
owning file. The result must change burden-state; it cannot merely restate that the TTP
was applied.
For hard/compound/deformed cases, release also requires enough owner-floor pressure to land
the profile actually routed: moral protest, imported criteria, source-worldview transfer,
higher-order reason or authority, testimony/transmission, predication/attribute pressure,
necessary-knowledge disputes, grief/register holds, and source-request cases each have their
own depth floor. Compactness removes padding, source parade, and framework dumping; it does
not license a smallest-compliant route-shaped answer. If the user asks for sources and a
routed burden depends on Qur'an/hadith evidence, use the text as an operator: quote or
precisely cite it, then state what diagnostic or restorative work it performs.
Scriptless/default render must not print raw `pressure_dimensions`, but it must satisfy the
same owner-floor idea in prose. Release fails when the answer names FPD, M1, V2, M8, P1,
a transmission owner, a predication owner, or a grief/register owner while leaving the
actual imported criterion, self-ground test, proof-status/warrant repair, source-frame
consequence, restoration vector, testimony/authentication pressure, predicate/category
pressure, or register-hold sequence unoperated.
When sources are requested, release also checks source-function coverage: the answer may not
use one decorative verse, hadith, or citation list to cover several routed functions. Each
source text must be tied to the pressure it lands, and missing hujjah, guidance, fitrah/ayat,
mercy/justice, repentance/return, testimony, or predicate-source functions remain PARTIAL.
Restoration and closing may synthesize only source functions that have already landed or
been explicitly held. They may not introduce the first operative mercy/justice,
worship-worthiness, repentance/return, testimony, or predicate-source correction after the
last state re-read. If that source function is still live, release it as a distinct
burden-local submove or next licensed burden before final response.
Hard-case release also checks the compact diagnostic opening: Layer A must reconstruct the
claim level, pattern/deformation, reason category, concealment, DO-orient, live burden,
source-status/noetic-frame, held/released state, and gate/release decision before Layer B
argues. A route-shaped answer with labels but no noetic frame is PARTIAL.
If a source-worldview frame supplies the criterion, release requires concrete frame
description from input anchors or bounded source knowledge before consequence trace. A
generic label such as "opponent worldview" without the operative commitment is source-frame
surface compliance, not M8 execution.
If the routed family pressure is not source-worldview, release must not manufacture a
worldview frame; testimony, predication, grief/register, kalamic proof-order, and other
family-local consequence traces remain distinct.

Owner-loadform gate: hard/multi-burden `ⁿBᵢ` release requires the selected
owner body or compiled bundle section to be loaded/read before the submove renders, unless
that exact section is already present in active context. Package availability, map presence,
or bundle co-location is not access. If the owner cannot be loaded or identified, do not
release a generic substitute; mark `PARTIAL / OWNER-BODY-NOT-LOADED` and name the
missing owner/path. This marker is permitted in default/hard output.

Family floor parity: `Family Execution Floor`, `Family Release Floor`, and
`Diagnostic Execution Floor` are release gates, not catalogue notes. If an individual
owner lacks a bespoke floor, the relevant family index supplies the fallback floor. A
case, diagnostic, tactic, technique, or procedure label cannot release output unless that
family floor is satisfied.

Use the runtime notation owned by `recursive-state-transitions.md`:
`B -> {s1...sn} -> Land(B) -> R -> Decision`; `sᵢ != Bᵢ`.
Gloss: one selected live noetic burden may contain multiple operative submoves; each `s`
preserves target -> operation -> result, then the whole `B` lands before state re-read.
Hiddenness, punishment/accountability, source-status, source-worldview, consequence tracing,
and identity-stabilization may belong to the same governing burden only as distinct bounded
submoves. Do not consolidate active TTP/operator functions into one generic operation block.
Restoration synthesis and any pastoral note release only after the active burden lands and
state re-read licenses closure, HOLD, PARTIAL, or the next input-anchored burden.
Identity-stabilization or source-status that is live and input-anchored must feed the
restoration vector or practitioner instruction; it must not remain a diagnostic orphan, and it
must not become speculative interior judgment.

Live-burden boundary is governed by the noetic burden being cleared. In a genuinely atomic
case, imported-criterion tribunal testing may include narrow hujjah/accountability or
guidance-as-coercive-proof submoves when their only function is to expose that tribunal. In a
dense hard case, do not presume those all belong to Burden 1 merely because they support the
same final indictment. If the input separately anchors accountability compression, hiddenness/
coercive-guidance demand, punishment/mercy/justice architecture, source-worldview consequence,
or worship-worthiness/predication pressure, the current burden must land and `R(H,Delta)` must
decide whether to release the next burden-cycle, HOLD/PARTIAL it, or close.
Multi-burden does not mean multi-recursion by default:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
They become separate burden-cycles only if `R` shows a new input-anchored `B` not already handled
as `s`. But `s` remains plural and operative: each active TTP receives a distinct target,
operation, and result before `Land(B)`.

Anti-overcollapse guard: the release gate must not turn a dense hard case into one omnibus
burden merely because several pressures support the same final indictment. If accountability
compression, hiddenness/coercive-guidance pressure, punishment/mercy/justice architecture,
source-worldview consequence, predication, transmission/testimony, grief/register, or
family-local proof-method pressure carries a distinct input-anchored target/function/restoration
vector, it must be released as its own burden after `Land(B) -> R(H,Delta)`, or explicitly
HOLD/PARTIAL. Compactness never licenses dropping that burden to keep the answer short.
First-order, second-order, and higher-order pressures are distinct release candidates when
they remain live: e.g. surface doctrine/report/predication objections; criteria or standards
judging those objections; and the meta-noetic source-worldview/register/source-status frame
that keeps governing after the local claim lands.
If the surface proposition is answered while its unreliable warrant-process or corrupt
foundation remains in place, release is incomplete.

When one burden requires more than three major operative submoves, run the submove saturation
gate from `recursive-state-transitions.md` as a cohesion audit, not as a count cap. If the next
move changes target-family, claim-level, source/noetic frame, claim cluster, or restoration
vector, the current burden must land and state must be re-read before the next burden is
released. If the additional move is merely available rather than materially necessary, HOLD or
PARTIAL rather than inflating Layer B. If it is materially necessary and cohesive, release it
as its own distinct target -> operation -> result. This gate prevents argument dumping; it must
not be used to erase a materially necessary TTP submove, consolidate active functions, or demote
a live identity/source-status implication into a label.

**Default Final-Output Preflight Gate (mandatory):**
Before emitting any default `/daee-epistemics` answer, scan the proposed final response
after release and render decisions but before output. This is a final-output gate, not a
render preference. If the proposed response contains prohibited scaffolding, route planning,
or meta-composition narration, the response is invalid and must be rewritten before output
as clean governed prose.

The Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It also
checks pipeline validity: internal diagnosis -> validated IR -> routed operator selection
-> output-release rubric -> diagnostic-render-contract -> state re-read -> post-render
gate -> STOP / HOLD / RECURSE / PARTIAL decision. Output-release decides what may be
released. Diagnostic-render-contract decides how it appears. Default final-output preflight
checks that the final answer obeys both. If the answer is clean prose but was produced by
topical essay sequencing, it is invalid and must be rewritten.

Pipeline-validity check:
- V1 / diagnosis ran before answer.
- Phase 2 passes ran where triggered.
- Diagnostic IR formed internally before routing.
- Routing came from validated IR.
- TTP selected as operator, not prose label.
- Output-release rubric applied before visible render.
- Render contract applied before final prose.
- state was re-read after the bounded move.
- Post-render gate run before closure.
- STOP / HOLD / RECURSE / PARTIAL decision made before ending.

Preflight recursion check: after the first bounded move, ask what cleared, what remains
live, whether the remaining live burden was already present in the original input, whether it is
now eligible, and whether any stop/register/semantic/thin-basis gate blocks it. If another
eligible same-input live burden remains after the current blocker clears, default output must
continue with one bounded next pass using a prose state transition, or render partial
release-status prose if limits prevent doing so. It may not silently close.

Preflight NewB check: the next burden may be released only when the re-read passes the
NewB license test: prior burden landed through owner-specific operation, cumulative-state
delta is visible, the next burden is input-anchored or held, the next burden differs from
the prior burden by live target/function rather than topic label alone, and no gate blocks
release. If the next material does not pass this test, it remains a submove, HOLD, or PARTIAL.
Practical application, source maps, concise response wording, do/don't guardrails, warning
paragraphs, and recaps of material that already landed are not NewB by default. Attach them to
the current Layer B when they pressure the current burden, or place them in Restorative/Application
Response or Closing Formulation when they package landed material. Release a new burden only
when `Land(B) -> R(H,Delta)` proves a distinct unresolved noetic function remains.
The user's request to "respond," "deal with this," "bring sources," or "dismantle the belief
system" does not by itself create a late practical-handling burden. It requires source-operation
inside the relevant burdens and a usable Restorative/Application Response. Practical handling is
NewB only when the input itself contains an unresolved practitioner constraint that cannot be
handled by the earlier burden and final response.
A belief-system/source-worldview request is different from practical handling. If the named
frame supplies the criterion, source-authority, or moral/evidential court, or the user explicitly
asks to dismantle that belief system, bounded source-worldview consequence must land as a local
submove or licensed burden, be explicitly held with reason, or be marked PARTIAL. Holding "full
movement taxonomy" does not hold the operative source-worldview burden.
Hard source-request cases must not compress distinct source functions into one citation stack.
If one burden uses multiple sources for materially different functions, separate their operation:
why the source is live, what premise/criterion/warrant it pressures, and what state change it
produces. A source map belongs after the functions land; it cannot substitute for them.

Same-burden collapse must preserve operator identity. If multiple TTPs/operators are live
inside a valid burden, each materially active submove remains visible under Layer B with:
why it is live for that burden, its target, its operation, its result/state change, and how
the result contributes to `Land(B)`. Do not replace actual matched owners/TTPs with generic
verbs. FPD, M1/M1P, M8, M9/predication discipline, V2, P1/P7, transmission/testimony,
grief/register, and family-local proof-method operators stay distinct where structurally active.
In moral-tribunal or worship-veto burdens, M3 can accompany orphaned moral intuition analysis
only after M1/M1-P is executed or explicitly cleared. If the burden uses M3 while skipping
self-grounding / performative-veto pressure, release fails. In final practitioner/restorative
handling, P1/P7 or the relevant procedure owner must surface when restoration, warning,
invitation, HOLD, STOP, or closure discipline is doing real work.

For the canonical valid default-mode transition example, use
`recursive-state-transitions.md`.

TTP labels do not satisfy execution. A default answer may briefly name an operation/module
label if helpful, but the operation must be visible: bounded target, operation performed,
and result of the operation. Operative submoves inside the same live burden feed the burden landing;
state re-read comes before any next live burden-level operator, not after every internal step.
In short: live burden -> operative submove target -> operation -> result -> burden landing -> state re-read.
Naming M1, M8, M9, or any other route label without that bounded operation is noncompliant.
A TTP label is not execution. The label may be hidden in default mode; if mentioned briefly,
it must be accompanied by the actual operation.
`Operation:` lines must begin with one of the closed operative verbs: `split`,
`distinguish`, `test against own grounds`, `disambiguate`, `classify`, `audit`,
`reclassify`, `narrow`, `expose`, `re-read`, `sequence`, `refuse jurisdiction of`,
or `clear`. Generic verbs such as `address`, `discuss`, `explore`, `engage`, or
`consider` are non-operative operation verbs and do not prove execution.
TTPs execute across refreshed case-states, not as a one-time itinerary from the initial read:
after each bounded operator lands, re-evaluate remaining same-input live burdens and held routes.
Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future contingencies
stay held with a release condition.

**Source-status & noetic-frame release check:**
Before releasing any source-backed claim, confirm:

```text
- one operative noetic frame is selected for this burden-cycle
- N_AT aliases count once; they are not multiple warrants
- N_Ashʿarī[*] and N_Māturīdī[*] are family labels, not automatic operative N
- family label != operative N
- shared vocabulary != shared warrant
- contradictory schools are not stacked as one operative authority
- contrast / opponent-position / historical-note / genealogy / held / bounded-comparison
  sources are not used as operative warrant in the same burden-cycle without explicit
  reclassification
- in default output, school, author, citation, genealogy, external philosopher, theologian,
  framework, or source-context references are not public-render material unless explicitly
  requested by the user or required by validated source-comparison IR
- source-heavy files do not create source-heavy default output; source heaviness is not
  public-render permission
- default citation allowance is restricted to Qurʾān, Sunnah, and sound narrations from the
  Salaf, and any such use is directly referenced through an external source
- Qurʾānic or ḥadīth evidence quoted for operative work is formatted cleanly where practical:
  Arabic when useful, translation, source/reference, then its diagnostic or restorative function.
  Prefer precision texts that name the mechanism; do not add citation padding, and do not collapse
  a central revealed text into a long prose sentence.
- `Islamic scholar` and `Islamic scholarship` are not umbrella terms for kalām, falsafah, or
  later speculative-theological figures; use specific source-status labels instead.
- umbrella terms (`classical theology`, `the classical tradition`, `mainstream kalām`,
  `Ashʿarī/Māturīdī tradition`) are not used as if they named one operative authority on
  a school-sensitive claim
- intra-school flattening is not used on a claim that is internally disputed
- agreement across frames, when asserted, is marked as substantive or verbal
- any non-operative source-status named in Layer B ends with an `Operative warrant:`
  sentence containing the specific non-premise clause: the non-operative source does
  not contribute to this warrant; specifically, the named element is not used as a
  premise here
```

If any line fails, rewrite before output. This is a release failure even when the prose is
clean. Authoritative wording is in
`references/diagnostics/recursive-state-transitions.md ?Source-Status & Noetic-Frame
Non-Equivalence Discipline`. This release check is universal across modes.

**Grounded noetic re-read release check:**
Before emitting any `state re-read` / `noetic re-read` (compact field block or prose
equivalent), confirm:

```text
- `burden landed` traces to an immediately preceding operative submove with
  target -> operation -> result
- `still live` is anchored in the original input, prior held material, or the preceding
  collapse radius
- `held` names material that is or was held
- `recursion decision` is consistent with `still live` and `held`
- `next licensed live burden` is anchored in `still live` or held material; or `none`
  when STOP / HOLD
- cumulative-state delta is visible: what changed after the owner-specific operation,
  what narrowed or collapsed, and why any next burden is materially different
```

A formatted but ungrounded noetic re-read fails this check even when each field appears
populated. Authoritative wording is in
`references/diagnostics/recursive-state-transitions.md ?Grounded Noetic Re-Read Shape`.

**Layer A / Layer B release checks:**
Layer A may expose only enough diagnostic state to make the current pass auditable. It names the
compact DSL/IR anchors, governing burden, current bounded operator, held routes, and remaining
input-anchored burdens when those facts govern release. Layer A must not smuggle the answer to held
downstream content.
Layer B may release only the current live burden's permitted result and any justified internal
operative submoves needed to land that burden. If Layer B begins answering a genuinely downstream doctrine,
source question, restoration synthesis, or new noetic aspect before the active burden landing and
state re-read, release has outrun routing. Hujjah/accountability or hiddenness correction is not
downstream smuggling when it is narrowly serving the active imported-tribunal burden; it is smuggling
when it becomes a broad doctrinal answer before that burden lands.

Held means semantically held, not merely labelled. A noun phrase listed in Layer A `held`
or `Held routes` must not appear in Layer B as an answered topical commitment unless a
preceding state/noetic re-read explicitly releases it with `Released: <item>`,
`Released routes: <item>`, or `Newly released routes: <item>`. It may be mentioned only
as still held, withheld, or contrast. Otherwise the response has held-route semantic
leakage.

Before emitting a default response, check:

```text
Layer A ? Compact DSL/IR header is present
read status, confidence, claim_level, pattern_profile, reason-category, concealment,
deformation, DO-orient, live noetic burden, current bounded operator, held,
source-status/noetic-frame, and gate/release decision are present
decisive missing differentiator is present when required
Layer B answers only the permitted current live burden and its justified operative submoves
Layer B includes Hidden Premises and a Core Formulation local to each released operation
Core Formulation identifies how sound/innate reason was deformed/concealed/deviated from, the modality/pattern of unsoundness, and the restoration vector
released burden is burden-complete: materially necessary sub-burdens receive matched TTP/operator treatment before R
no headline-only answer, skipped internal sub-burdens, generic prose substitute, or broad-conclusion jump
Land(B) is supported by owner-specific operation and cumulative-state delta
Restorative Response appears once after the final state/noetic re-read and releases no held downstream burden
Restorative Response identifies restored order, restored criterion/source/warrant placement, relieved deformation/concealment, and what remains held
Closing Formulation appears once at the end after Restorative Response
Closing Formulation does not substitute for state/noetic re-read or self-close each burden
non-trivial operators include compact owner-ID-bearing TTP/operator trace when needed
active owner/TTP submoves label the local owner ID where one exists (for example, `¹B₁ [FPD]`, `¹B₂ [M1]`, `¹B₃ [M9]`; ASCII `1B1` fallback only if needed)
generic "Operative submove N" labels do not satisfy module-backed owner execution when an owner ID exists
post-hoc TTP trace lists do not satisfy execution unless owner IDs already appeared on the local submoves
more-than-three major operative submoves trigger the submove saturation cohesion audit
additional cohesive necessary submoves remain distinct target -> operation -> result units
submove saturation is not a merge license; active TTP/operator functions remain distinct or the output is PARTIAL
TTP entry criteria were met
TTP exit criteria produced a result
TTP owner-specific operation floor was satisfied
State/noetic re-read decided STOP / HOLD / RECURSE / PARTIAL internally
```

If any line fails, rewrite before output. This is a release failure even when the prose is clean.

Bounded does not mean tiny; clean prose does not mean shallow; no ledger does not mean no recursion.
Do not optimize for shortness by skipping an eligible same-input burden. Default output
may be longer in complex cases when the refreshed gate requires multiple bounded passes, but it
must remain pass-by-pass and may not become a comprehensive essay dump.
For hard, compound, or deformed scriptless compact-DSL cases, release sufficiency requires enough rendered
diagnostic, theological, and restorative substance for each input-anchored burden to land.
Anti-padding language cannot be used as a shortest-output target, cannot hide a warranted
per-burden Layer A re-entry, and cannot turn a materially live worldview/identity criterion
into a brief source-status label.
Do not close with Restorative Response or Closing Formulation while `R(H,Delta)` names a
remaining input-anchored burden that is now eligible. Continue with the next bounded pass,
or mark PARTIAL with the next live burden when response/tool/interaction limits block it.
For release purposes, supporting premises and contrast rules named in the user's input count
as input-anchored material once the blocker that held them clears; do not treat them as new
future questions solely because they were not phrased as separate requests.
If the state re-read lists remaining input-anchored burdens, "only if requested" is not a
release decision unless a named hold gate blocks release. "Requires its own bounded pass"
is a continuation or PARTIAL reason, not a closure reason.
The release target is governed recursive sufficiency: complete-enough restoration of the live
same-input noetic structure under the DSL/IR gates, not shortness, length, or topic coverage for
its own sake.
Within those gates, the skill should address as many input-anchored live burdens and materially
active submoves as the case makes available. No-excess release forbids padding, owner dumps, and
unlicensed doctrine; it does not license consolidation of active burdens or TTP/operator
functions into fewer operations. If the output cannot traverse the remaining live structure, it
must name the next live burden and blocked submove(s) as PARTIAL rather than close.
PARTIAL requires concrete limit reason: name the live burden and the response/tool/interaction
limit preventing traversal. A bare PARTIAL label is not a release decision.
This is the output-release form of `anti-patterns.md` Route Surface-Compliance Failure Failure.
It also prevents `anti-patterns.md` Clean Essay Surface-Compliance Failure: clean prose is valid only if pipeline
execution is visible through prose, not through a topical itinerary.
Moving from the current live burden to downstream doctrine requires state re-read prose; hidden premises
listed without operator result do not satisfy the release gate. Moving from imported criterion
to a narrow accountability or hiddenness-frame correction inside the same tribunal burden requires
target -> operation -> result, then burden landing -> state re-read before any new live burden.

Default final-output failure tokens include:
- "Now I have enough", "I now have enough", or "I now have sufficient".
- "Let me compose", "Let me write", "Let me craft", or
  "Let me construct the diagnostic IR".
- `## Diagnostic IR`, `[Diagnostic IR]`, `Case State:`, a full IR/case-state field block,
  `matched_modules`, `source_basis`, load ledger, route ledger, planned route list, or
  a visible route plan such as `Next: FPD -> ...`.
- Literal default governance fields such as `Recursion decision:`, `next_eligible_pass:`,
  `post_render_gate:`, or `Governance:`. Raw field labels are for `:dsl`, internal/development
  audit, pass-review, or diagnostic trace. Default mode uses prose transition plus bounded next
  pass, and may use compact target-explicit control-bound markers such as `R(H,Δ): RECURSE`,
  `Δκ live`, `∇·κ positive/live`, `∇×κ unresolved`, `∇·B positive`, or `∇×ξ unresolved`.
- Smoke/runtime proof boilerplate such as "Smoke runtime note", "Runtime grounding detail",
  "Skill invocation proof", "loaded before output", or "proof of loaded files" in the
  public default output. Runtime proof belongs in trace/verdict artifacts, not Layer B.
- Smoke/test scaffold phrases such as "this smoke artifact", "runtime constraint being
  tested", "owner floor is applied", "owner-floor pressure", "the TTP has to change
  something", "burden-completeness check", or "the operation is bounded to the target
  named above" in the public default output. These are verdict/trace language, not
  runtime answer language.
- Route/check harness phrases such as "execute queued owner", "execute first-live owner",
  "owner-floor passed", "validation passed", `smoke_kind`, `validation_fidelity`,
  `execution_fidelity`, `route_plan`, `features.json`, `check_execution`, or repo/dev
  harness proof claims in canonical scriptless output. Owner identity may appear only as
  a human-facing local submove anchor, not as a harness command or validation verdict.
- Literal `Owner-floor:` lines and `B<N>.s<M>` legacy/checker markers as the primary public
  notation. Canonical scriptless output should use `¹B₁ [owner ID] - plain operation`;
  use `1B1` only as an ASCII fallback when Unicode is unsupported, with target,
  operation, and result in case-specific prose.
- Formula boilerplate such as "That test changes the force of the case", "The result is
  a real state change", "What remains after that change is not forgotten", or reusable
  target/operation/result prose repeated across burdens. Default output must answer the
  case; it must not sound like a filled compliance frame.
- Reusable hinge/load-bearing boilerplate such as "load-bearing point", "if that point
  is left vague", "this exact pressure can stand", "surrounding topic is held back",
  "the live hinge can be tested", "case-state after this pressure", or "the move
  forces the inference to carry its own burden". These are proof-of-execution phrases,
  not user-facing default answer language.
- Cross-fixture or copied-example contamination. Default output must not import a
  named source-worldview hard-smoke frame, quoted hard-smoke phrases,
  accountability/punishment/hell, source-biography, moral-protest, or hiddenness
  language from another example unless the current input and validated IR release
  that burden-family.
- Strong interior-classification verdict dumps such as `Concealment: iʿrāḍ primary`,
  `Deformation: hawā primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. The compact lowercase Layer A fields are
  allowed only as bounded DSL/IR anchors.
- A bibliography, "Primary Sources Referenced", external research-style source list, or
  source-basis ledger in default mode unless sources/citations were requested.
- Bare "Step 1 / Step 2 / Step 3 / Step 4" or "Move 1 / Move 2 / Move 3" sequencing
  when offered as recursion.

Rewrite-before-output rule: if the proposed default answer fails the preflight scan, do not
emit it. Rewrite it into the mandatory compact DSL/IR header plus bounded governed response:
Hidden Premises, per-operation Core Formulation, Bounded Response / operative submoves,
State/noetic re-read, one Restorative Response, and one final Closing Formulation. Name the
governing diagnostic fact, release only the current permitted move, include a prose state
transition if same-response recursion is internally active, and omit the raw IR, case state, matched route,
route plan, scholar/source parade, school-label context, genealogy, and public external-theorist support.

---

## Release Question

Before releasing any content, ask: *Is this response releasing the right content, in the right order, for the current refreshed case-state ? no more, no less, not before upstream blockers clear?*

---

## Post-Render Re-Entry Gate

After every bounded restorative move, before closing the response, run the state re-read /
Re-Entry Gate and populate the internal IR `post_render_gate`. The literal field shape below
is an internal control shape and may be visible only in `:dsl`, internal/development audit, pass-review, or
diagnostic trace. It is not a default output template:

```text
post_render_gate:
  cleared_this_pass:
  remaining_live_distortions:
  held_routes_rechecked:
  newly_released_routes:
  next_eligible_pass:
  recursion_decision: STOP | HOLD | RECURSE | PARTIAL
```

The gate must answer:

1. What was cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. Is there a next eligible pass?
6. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

Decision rules:

- `STOP`: valid only if no live distortion remains, no eligible live burden remains, and no held route has become eligible.
- `HOLD`: valid only if remaining material exists but its release signal is absent from the input.
- `RECURSE`: required if another live distortion remains in the same input or a held route becomes eligible.
- `PARTIAL`: required if token, tool, or interaction limits prevent completion while recursive pressure remains.

STOP cannot be emitted before this gate runs. Held material must be rechecked after each pass.

Default mode must not print `Recursion decision: RECURSE` as proof of compliance. If internal
recursion is active, the answer must perform the transition in prose and then execute one bounded
next pass. If limits prevent that pass, render partial release-status prose or a compact
control-bound marker such as `R(H,Δ): PARTIAL` rather than dumping a raw field label.

---

## Pass/Fail Checks

### 1. Governing Burden Identified

**Pass:**
- The response identifies the live governing blocker or pressure family.
- The response does not answer a downstream doctrinal question before the upstream blocker clears.
- The visible topic is not mistaken for the governing issue.

**Fail:**
- The response treats the visible topic as the governing issue while ignoring a stronger upstream blocker.
- The response answers first-order content while semantic, lexical, authority-order, proof-method, tribunal, register, or stop pressure remains unresolved.

**Upstream blockers that must clear before downstream release:**

| Blocker | Owning file |
|---------|-------------|
| Lexical-ontological trap / loaded term | `tactics/M9-predication-mode.md` |
| Semantic neutralization (recontenting / evacuation) | `diagnostics/prophetic-discourse-neutralization.md` |
| Authority-order inversion | `diagnostics/foreign-premise-detection.md` ?O-1 |
| Imported criterion or tribunal | `diagnostics/foreign-premise-detection.md` |
| Static-perfection tribunal | `diagnostics/perfection-criterion-usurpation.md` |
| Proof-method overreach | `diagnostics/proof-method-audit.md` |
| Definition / conception capture | `diagnostics/definition-discipline.md` |
| Causal-series confusion / regress | `diagnostics/causal-series-taxonomy.md` |
| Necessity/contingency proof-grammar overreach | `diagnostics/proof-method-audit.md` |
| Composition / dependence pressure | `case-library/do-attribute-precision.md` via `tactics/M9-predication-mode.md` |
| Occurrence-to-createdness collapse | `diagnostics/kalamic-interlocutor.md` |
| Over-intellectualization / abstraction-as-cure pressure | `anti-patterns.md ?Transcendence Default / Abstraction-as-Cure` |
| Grief / register hold | `procedures/P7-restoration-stops.md` Stop 1 |
| Thin-basis underdetermination | `procedures/P7-restoration-stops.md` Stop 4 |

---

### 2. No Excess Release

**Pass:**
- The response releases a bounded but burden-complete corrective move for the current refreshed state.
- "Sufficient" is measured by landed live burden-state, not by brevity. In a hard, compound,
  or deformed case, the required corrective move may be a full burden-cycle with
  several operative submoves, revealed-text operation where the mechanism is named, and a
  visible re-entry before the next released burden.
- "Bounded" never means consolidating distinct active submoves. If several
  input-anchored operator functions are materially active inside the current burden, each
  receives its own target -> operation -> result or the response marks PARTIAL.
- It does not expose more framework machinery than the case requires.
- It does not stack arguments after the governing move has landed.
- It does not convert restoration into a concession press.
- It does not expand merely because more owners or proof-lines are available.

**Fail:**
- The response dumps multiple owners, arguments, diagnostics, or proof-lines when the case only required one governing move.
- The response continues after recognition or contact has surfaced.
- The response escalates into theoretical density when a bounded corrective move would suffice.
- After FPD/M1 clears an imported criterion, the response automatically releases all
  downstream doctrinal content rather than internally choosing STOP, RECURSE, HOLD, or PARTIAL at
  the post-render gate.
- The response ends default mode with a bibliography, source list, "Primary Sources
  Referenced", or source-basis ledger even though the user did not request sources and
  the task is not internal/development audit or research.

---

### 3. All Live Upstream Requirements Satisfied Before Downstream Release

Downstream content must remain held while any of the following are active:

- Loaded term / lexical trap → disambiguate before answering yes/no
- Imported perfection or static-deity tribunal → refuse tribunal-status before attribute content
- Semantic neutralization of revelation → handle that blocker before first-order interpretation
- Authority-order inversion → route through O-1 before ordinary reason/revelation tension
- Proof-method pressure → audit the proof architecture before deploying the proof
- Definition capture → clear public-language vs. technical capture before the contradiction claim
- Causal/regress pressure → classify the series before cosmological-argument prose
- Occurrence-to-createdness collapse → separate occurrence, divine act, product, and modality first
- Composition/dependence pressure → clear lexical/category/definition discipline first
- Necessity/contingency proof grammar → audit what the proof can and cannot establish
- Over-intellectualization → check whether live need is restoration, recognition, testimony, practice, or order of the knower; do not answer with more abstraction
- Grief/register hold → do not deploy intellectual content as though it were a seminar question

**Fail condition:** Any of these blockers active when doctrinal content is released.

---

### 4. Held Material Is Actually Held, Then Reassessed

**Pass:**
- Downstream material may be named as downstream but not fully released before its governing conditions are met.
- Holding is pass-scoped and traversal-scoped, not permanent suppression.
- `H(n+1) = (Hn ∪ InputLive_n) - Released_n`: what is cleared, held, and not yet permitted stays explicit.
- After the current `B` lands, `R` reassesses held material.
- If held material remains live and now governs, it becomes the next bounded pass; if not, it is dropped, compressed, or resolved.

**Permitted formulation:**

> X governs first; Y is live but held; Z is downstream and not yet released.
> After X is addressed, refresh state. If Y still governs, Y becomes the next bounded pass.

**Recursive rule:** after X is addressed, `R` determines whether held Y remains live and
becomes the next governed pass. Gloss: recursion may move through one noetic structure's
concealments and distortions, but each movement is ordered, justified, and bounded.

**Fail:**
- The response says a downstream issue is held, then effectively answers it in the same pass anyway.
- The response treats held as never answer.
- The response treats held as only waiting for a new user reply.
- The response recurses into downstream issues without refreshing case-state.
- The response treats recursion as permission to dump every downstream argument at a single state re-read.
- The response bypasses Layer A / Layer B discipline by answering all burdens at once.

---

### 5. Recursive Traversal Discipline

**Pass:** The response may proceed through multiple burdens only by governed traversal:

```text
B -> {s1...sn} -> Land(B) -> Δ/field diagnostics -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

Gloss: identify the current blocker, apply the matched owner/TTP, land the burden, refresh
state, release the next item only if it remains live and now governs, and run the post-render
gate before closure. STOP only when P7 / register / semantic / sufficiency governance permits it
and no next eligible pass remains.

Recursive burden-cycle shape for expanded diagnostic/internal audit render:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded move:
state re-read:
Release status: prose closure/hold/partial/continuation status plus compact `R(H,Δ): RECURSE/PARTIAL/COMPLETE` marker when control-relevant
```

Default compact DSL-governed answers may compress this shape, but the state re-read and decision still govern.

**Fail:**
- The response collapses recursive traversal into a single argumentative dump.
- The response treats every detected issue as immediately releasable.
- The response fails to explain how the movement restores order.
- The response keeps visiting downstream burdens after restoration or contact has already landed.
- The response holds downstream material but never reassesses it after a governing blocker clears.
- The response stops after one strong move without running the post-render gate.

---

### 6. Bounded Layer B

**Pass:**
- The public answer gives the bounded but burden-complete Layer B corrective move for the current pass.
- In hard cases, the sufficient Layer B move is the amount needed to perform the active
  owner-floor operation(s), not the shortest paragraph compatible with the heading.
- It avoids unnecessary diagnostic labels, owner names, PF codes, or theoretical explanation unless the case or user request calls for diagnostic visibility.
- It remains case-sensitive rather than globally templated.
- It may use compact lab-report form, but only with fields that materially serve the case.

**Fail:**
- The response turns internal machinery into the public answer without need.
- The response prints a full diagnostic structure by default when burden-accounted release only needs
  compact governance visibility.
- The response confuses patch-report format with runtime skill output.
- The response treats diagnostic transparency as permission for exhaustive machinery exposure.

---

### 7. Post-Render STOP / HOLD / RECURSE / PARTIAL Decision

**Pass:**
- `Land(B) -> R` runs before any closure decision.
- `R(H,Δ)` records what cleared, what remains live, which held routes were rechecked, and whether any route became newly eligible.
- STOP only when no next live distortion remains and P7 permits closure.
- HOLD when another pass is live but release is blocked.
- RECURSE when the current pass clears an upstream blocker and another burden remains live unless a stop/hold/gate/limit blocks it.
- PARTIAL when limits prevent the next eligible pass; name the next eligible pass.
- The response preserves P7 stop discipline.
- The response does not continue merely because additional related issues are available.

**Fail:**
- The response keeps expanding after the governing move has landed.
- The response answers every related issue because it is available, rather than because the refreshed case-state requires it.
- The response turns a restorative contact into a verbal concession press.
- The response treats stop discipline as permanent refusal when a refreshed state would permit a later bounded pass.
- The response emits STOP while `remaining_live_distortions` or `newly_released_routes` is non-empty.
- The response emits STOP because of token/tool limits while recursive pressure remains; this must be PARTIAL.

---

### 8. Diagnostic Render Eligibility

**Pass ? compact diagnostic render is allowed or preferred when:**
- The user invokes `/daee-epistemics:dsl`.
- The user asks for diagnostic transparency.
- The user invokes plain `/daee-epistemics`; the default compact DSL/IR header is mandatory.
- The case involves multiple live burdens.
- The case requires held/downstream distinction.
- Recursive traversal needs to be visible.
- An internal/development audit, regression, or pass-review is being performed.
- The response needs to show why a downstream answer is not yet released.
- The user is testing whether the skill routed correctly.

**Fail:**
- The response uses a full lab-report layout when burden accounting only requires a bounded corrective answer.
- The response hides necessary routing information when the user explicitly asked for diagnostic skill execution.
- Plain `/daee-epistemics` is treated as a giant ledger or full IR dump by default.
- The response exposes all possible fields rather than the materially governing fields.

---

### 9. Not a Mandatory Full-Field Template

This rubric governs output release. It does not impose a mandatory full-field public format. Runtime output remains governed by validated IR, bounded Layer B, diagnostic render eligibility, recursive state re-read, and STOP / HOLD / RECURSE / PARTIAL discipline.

Do not convert patch-report requirements into the skill's normal runtime response format.

Compact diagnostic structure is mandatory in default at the frame level and may be expanded only when it serves the case. Exhaustive field materialization is not permitted unless the task is internal/development audit, regression, pass-review, or explicitly diagnostic.

---

## Failure Tests

### FT-1 ? Loaded term
**Input:** Is God a body?
**Bad output:** Yes/no answer before disambiguating body/jism.
**Required behavior:** Split the loaded term (ordinary and technical senses) before doctrinal answer; block false sense-shift; hold downstream attribute content until cleared.

### FT-2 ? Static perfection tribunal
**Input:** A God who speaks or acts in time cannot be perfect.
**Bad output:** Generic attribute answer or anthropomorphism answer before handling imported perfection tribunal.
**Required behavior:** Identify imported/static perfection tribunal; refuse tribunal-status; then route downstream to speech/action, predication, composition, or attribute content as appropriate.

### FT-3 ? Semantic neutralization
**Input:** We affirm the text, but it gives no determinate guidance here.
**Bad output:** First-order interpretation before handling semantic neutralization.
**Required behavior:** Distinguish ordinary interpretation from guidance-nullification; handle semantic neutralization before downstream interpretive content.

### FT-4 ? Authority-order inversion
**Input:** Reason validates transmission, so reason can overrule transmission.
**Bad output:** Treating this as ordinary reason/revelation tension.
**Required behavior:** Route through authority-order inversion (O-1); distinguish sound reason supporting transmission from imported rational tribunal subordinating it.

### FT-5 ? Composition/dependence pressure
**Input:** Real attributes make God composite and dependent.
**Bad output:** Doctrinal attribute answer before clearing lexical/category/definition pressure.
**Required behavior:** Identify loaded terms (composition, parts, dependence, other-than); check ordinary/technical/equivocal use; block illicit move from conceptual distinction to separable parts; only then release attribute content.

### FT-6 ? Causal regress
**Input:** An infinite causal regress is impossible, therefore...
**Bad output:** Cosmological-argument prose before classifying the regress.
**Required behavior:** Classify causal-series / infinity / dependency claim; distinguish simultaneous vs. successive series; distinguish causal regress from numerical infinity; then decide whether proof prose is permitted.

### FT-7 ? Necessity/contingency overreach
**Input:** The necessary existent proof establishes the whole doctrine.
**Bad output:** Allowing proof grammar to become total doctrine.
**Required behavior:** Audit proof-method; identify what the proof can establish and what it cannot; prevent proof-method from becoming primary epistemic basis.

### FT-8 ? Over-intellectualization
**Input:** Give a deeper theoretical answer.
**Bad output:** Escalating abstraction automatically.
**Required behavior:** Check whether live need is restoration, recognition, testimony, practice, or order of the knower; do not answer with more abstraction if abstraction-as-cure pressure is live.

### FT-9 ? Diagnostic machinery dump
**Input:** /daee-epistemics Is God in a direction?
**Bad output:** Full exhaustive template with every case-state field, all modules, and long proof expansion.
**Required behavior:** Compact DSL/IR header required; loaded term governs first; downstream attribute content held; only materially relevant fields shown.

### FT-10 ? Held-but-answered contradiction
**Input:** Do attributes imply composition? Also answer whether the doctrine is coherent.
**Bad output:** Says composition is upstream and held, then answers full coherence downstream.
**Required behavior:** Composition/dependence pressure governs first; coherence answer downstream and held until lexical/category discipline clears.

### FT-11 ? Patch-report leakage
**Input:** /daee-epistemics Why is secular neutrality not neutral?
**Bad output:** Full changelog-style report with files inspected, proof table, and implementation verdict.
**Required behavior:** Runtime compact diagnostic response, not patch report.

### FT-12 ? Template-driven routing
**Input:** /daee-epistemics Is God a body?
**Bad output:** Fills every field in the diagnostic template and thereby implies routing was done.
**Required behavior:** Validated IR/routing first, render second; fields only surfaced if materially helpful.

### FT-13 ? Held-as-never-answer
**Input:** /daee-epistemics Is God a body? Also explain whether divine attributes imply composition.
**Bad output:** Loaded term governs first. Composition is downstream and held. Response ends permanently with no reassessment rule.
**Required behavior:** Disambiguate body/jism first. Refresh state. If composition/dependence pressure remains live, it becomes the next bounded pass. If the loaded-term clarification dissolves the composition pressure, compress or drop it.

### FT-14 ? Recursive dump
**Input:** /daee-epistemics Is God in a direction? Also, doesn't that imply body, place, limit, and composition?
**Bad output:** Answers direction, body, place, limit, and composition all at once with a full attribute treatise.
**Required behavior:** Identify the governing loaded spatial term. Clear semantic/lexical discipline first. Refresh state. Only release the next pressure if it remains live and no stop/hold/gate blocks it.

### FT-15 ? State re-read-as-user-reply-only
**Input:** /daee-epistemics Refute secular neutrality.
**Bad output:** Names imported tribunal, says all downstream positive reconstruction is held, and refuses to proceed unless the user replies.
**Required behavior:** Clear the false neutrality tribunal. Refresh state inside the response if the current answer itself sufficiently clears the criterion. If sovereignty-regress or authority-order remains live and eligible, release a bounded next move. Do not dump every political-theology argument.

### FT-16 ? Stop discipline after recognition/contact
**Input:** Interlocutor admits: "Okay, I see secular neutrality is not neutral. What follows?"
**Bad output:** Launches a long cumulative proof stack.
**Required behavior:** Recognition/contact has surfaced. Stop concession pressure. Offer one bounded next move or one clarifying invitation.

### FT-17 ? Premature closure without re-entry
**Input:** /daee-epistemics The moral objection is really that modern liberal equality is the judge of revelation. Also, if that standard falls, what should govern the question instead?
**Bad output:** Correctly exposes the imported tribunal, then closes as though the whole case is complete.
**Required behavior:** Clear the imported tribunal, run the post-render gate, recheck held routes, and identify whether the positive criterion-order pass is now eligible. If eligible and no stop/hold/gate blocks it, continue with one bounded next move. If limits prevent it, render partial release-status prose rather than closing.

### FT-18 - Essay sequence mistaken for RECURSE
**Input:** /daee-epistemics The objection says disbelief, hiddenness, accountability, punishment, and mercy all make Islam morally impossible.
**Bad output:** The answer uses "Move 1", "Move 2", "Move 3", and "Move 4" headings, but no refreshed-state transition explains what cleared, what remains live, why the next live burden is eligible, or why continuation rather than prose closure/hold/partial status governs.
**Required behavior:** Use ordinary prose if in default mode, but include the state-change relation before the next pass. A short sentence is enough: "That clears the criterion question; the remaining already-present issue is X, so the next bounded move is Y."

### FT-19 - TTP label without TTP execution
**Input:** /daee-epistemics Use the M1 and M8 moves on this worldview objection.
**Bad output:** The answer says "the M1 move" or "the M8 move" while the paragraph behaves like an essay section or worldview critique rather than the bounded operator selected by the validated IR.
**Required behavior:** Select the TTP from case-state, give it a bounded target, perform the specific operation, refresh state, and release the next TTP only if the post-render gate makes it eligible. Default mode may name the operation briefly but must not print a route ledger.

### FT-20 - Route chain as current bounded operator
**Input:** /daee-epistemics A moral protest argues that God is cruel, hidden, and not worthy of worship.
**Bad output:** `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`.
**Required behavior:** Complete diagnostic reduction before routing. Then name one burden-level operator such as `imported-criterion tribunal test` or `worship-worthiness criterion test`. Route chains remain internal routing context, not the current bounded operator.

### FT-21 - Operative submoves mislabeled as burden-cycles
**Input:** /daee-epistemics Same moral protest, with hiddenness and accountability assumptions.
**Bad output:** Pass 1 is FPD, Pass 2 is M1, Pass 3 is DO-8, Pass 4 is M8, and Pass 5 is restoration, all before any Burden-1 state re-read.
**Required behavior:** Treat owner/TTP route legs as operative submoves under the current burden only when `R(H,Delta)` or submove saturation proves the same target/function/source-frame/restoration vector. Same moral indictment is not enough. In hard compound source-request cases, accountability/hujjah, hiddenness/coercive-guidance, punishment/mercy/justice, predication, source-worldview, testimony, or family-local proof-method pressure must be released as a later burden-cycle, HOLD/PARTIAL, or kept as a local submove with that same-function proof. Burden 2 begins after Burden 1 lands, state re-read runs, and a next input-anchored noetic function is licensed.

### FT-22 - Shallow live-burden execution
**Input:** /daee-epistemics Use FPD and M1 on this criterion objection.
**Bad output:** The answer lists hidden premises and names the M1 move, then proceeds to doctrine without stating what the operation did to the live burden.
**Required behavior:** For each TTP inside the live burden, preserve target -> operation -> result; then land the burden with burden landing -> state re-read before downstream release.

### FT-23 - Restoration before state re-read
**Input:** /daee-epistemics This proves God is not worthy of worship.
**Bad output:** The answer gives restoration synthesis and a pastoral note before the worship-worthiness criterion has landed and before state re-read runs.
**Required behavior:** Land the active burden, run state re-read, and only then release restoration synthesis, pastoral note, closure, HOLD, PARTIAL, or the next input-anchored burden.

### FT-24 - Source architecture collapsed into final restoration
**Input:** /daee-epistemics A hard moral protest asks for sources and says divine mercy, justice, guidance, and worship-worthiness fail.
**Bad output:** The answer quotes one source during an upstream criterion pass, then closes with a warm paragraph about mercy and worship-worthiness without any burden-local source operation for mercy/justice, repentance/return, or the restored worship order.
**Required behavior:** Treat source functions as routed pressure, not closing color. If mercy/justice, repentance/return, guidance/non-compulsion, fitrah/ayat, testimony, or predicate-source work remains live after state re-read, render it as a distinct operative submove or licensed next burden with the source text immediately doing diagnostic or restorative work. If limits prevent that, mark PARTIAL with the unlanded source function.

### FT-25 - Family-local pressure flattened into generic worldview response
**Input:** /daee-epistemics A report-authentication objection, a divine-attribute predication objection, or a kalamic proof-order objection is presented with source/status language.
**Bad output:** The answer treats the case as a generic source-worldview or reason-repair problem, then gives a broad closing synthesis without testimony/tawatur, predicate/category, or proof-order operation.
**Required behavior:** Keep the pressure family local. Transmission cases must pressure testimony, tawatur, and authentication; predication cases must pressure category, zahir/ta'wil/majaz/haqiqah, and predicate use; kalamic/falsafi proof-order cases must pressure the claimed proof method and tribunal role. Do not flatten those families into moral-protest or source-worldview language merely because source-status language appears.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/diagnostic-render-contract.md` | Governs visible render shape after this rubric passes |
| `references/diagnostics/framework-pipeline.md` | Operative pipeline audit surface; shows release and post-render gate placement |
| `references/diagnostics/recursive-state-transitions.md` | Canonical abstract owner for STOP / HOLD / RECURSE / PARTIAL semantics |
| `references/diagnostics/routing-precedence.md` | ?VII distinguishes routing precedence from output-release and render |
| `references/procedures/P7-restoration-stops.md` | P7 stops govern current-pass deployment; this rubric governs release discipline |
| `references/diagnostics/diagnostic-ir.md` | IR fields `output_shape`, `what_is_withheld_and_why`, `what_remains_live`, `continuation_eligibility`, and `post_render_gate` carry the release state |
| `references/diagnostics/case-state-schema.md` | Concealment × orientation matrix governs register-hold discipline |
| `references/diagnostics/anti-patterns.md` | Anti-patterns for failure modes this rubric prevents |
| `skill/SKILL.md ?V.A` | Control-plane pointer to the owner files; this file owns release amount and held/released discipline |
