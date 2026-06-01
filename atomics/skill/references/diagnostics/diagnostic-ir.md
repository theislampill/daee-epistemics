---
id: diagnostic-ir
module_class: governance
canonical_path: skill/references/diagnostics/diagnostic-ir.md
contract_version: "0.4.0.0"
load_when:
  - any substantive engagement requiring routing — IR is not optional
routing_effects:
  - gates all module dispatch before any content module loads
emits:
  - routing_gate
catalogue_registered: false
---

# Diagnostic IR - Dispatch Gate and Typed Intermediate Representation

PACK-SPEC note: this file functions as an IR/dispatch contract owner. For future normative edits,
use `docs/spec-authoring-pack.md`; keep uppercase MUST / SHOULD / MAY intentional and backed by
examples or checks.

This file defines the complete typed state that must be formed before any content module is dispatched. It sits between the workflow layer (routing procedure) and the metaphysical-architecture layer (what is being restored). Its purpose is twofold:

1. Gate module dispatch. Dispatch is blocked until the mandatory minimum fields are populated and consistency checks pass.
2. Make routing auditable independently of prose quality.

The IR is not a retrospective record. Writing the IR after the response is cosmetic compliance. The
initial IR must govern dispatch before content release; the `post_render_gate` then refreshes that
same live control surface after a bounded move and before closure. If the initial IR cannot be
formed because mandatory fields cannot be populated, the correct action is Stop-4, not a response
with a post-hoc IR.
When a Closure/Reconstruction Witness will be rendered, its `Initial burden set` must be derived
from this pre-release Layer A / Diagnostic IR burden enumeration before terminal states are printed.
`R(H,Δ)` may discover newly live or next-pass burdens, but those are not retroactively inserted into
the original initial set.

The IR composes fields from several sources:

- Case-state fields from `references/diagnostics/case-state-schema.md`
- Claim-level and pattern-profile fields from `references/diagnostics/pattern-profiling.md`
- Reason-category fields from `references/diagnostics/reason-disambiguation.md`
- Backbone predicate emissions from `references/diagnostics/arabic-backbone-predicates.md`
- Foreign-premise detection from `references/diagnostics/foreign-premise-detection.md`
- Prophetic discourse neutralization from `references/diagnostics/prophetic-discourse-neutralization.md`
- Philosophical-usurpation fields from `references/case-library/philosophical-usurpation.md` when active
- Architectural layer disruption from `references/metaphysical-architecture.md`
- P7 stop status from `references/procedures/P7-restoration-stops.md`
- Routing-precedence state from `references/diagnostics/routing-precedence.md`
- Reconstruction verdict from `references/diagnostics/ir-reconstruction-pass.md`

---

## DSL-IR as Audited Formalization Layer

The Diagnostic IR is the repo's canonical audited formalization layer. It is where the live
noetic structure becomes actionable: claims, criteria, grounding relations, governing epistemic
rules, testimonial posture, interpretive filters, held routes, and restoration target are rendered
into one governable state before any content release.

This formalization does not claim that the whole structure is exhausted by a pure proposition
graph. Grounding relations may be read graph-like, and often locally DAG-like, but the audited
control surface must also carry weighting, suppression, underdetermination, semantic holds,
register holds, and release permissions.

Meta-noetic memetics gives the object-domain: how noetic structures and their governing
epistemic rules form, function, stabilize, defend themselves, mutate, reproduce, spread, and
instantiate linguistically through recurring slogans, labels, arguments, habits, institutions,
identity patterns, and social pressure. The IR gives the operative representation. It does not
encode the whole structure exhaustively; it encodes diagnostically relevant features of that
structure so routing, comparison, release, and restoration can be governed.

Identity-linked commitments may be represented only as part of that structure, not as a separate
route. Identity may be part of the noetic equilibrium, but it cannot by itself carry the verdict:
it may stabilize a criterion, authority posture, moral vocabulary, discourse orientation, or
collapse radius, while interior motive, sincerity, culpability, soul-state, and primary
load-bearing status remain held unless independently grounded.

Meta-noetic memetics becomes operational here through fields such as `Foreign premise`,
`Upstream findings`, `Claim-level`, `Pattern-profile`, `Structural pattern print`,
`Load-bearing node`, `Collapse radius`, `Concealment mode`, `DO-orient`,
`What is withheld and why`, and `What remains live`. Those fields do not replace the repo's
existing owners; they make dynamic interaction auditable by tracking what the structure treats
as basic, what counts as evidence or authority inside it, which inferences are permitted, how
beliefs support each other, how the structure defends itself, and what downstream claims must be
re-evaluated when a load-bearing node is cleared.

**Operationalization rule:** Meta-noetic memetics does not add a new routing pass. It is the
explanatory frame for the already-named dynamics. Its live IR surface is:

```text
surface discourse -> IR(N,m,τ,σ) -> ∇ route-gradient -> B -> TTP/operator -> Δ -> field diagnostics -> R(H,Δ)
```

Control-surface test: the vocabulary is valid only when it changes an existing field,
hold/release decision, collapse radius, load-bearing node, operator choice, or state re-read.

- `Foreign premise` and `Upstream findings`: tribunal-installation, criterion-smuggling, semantic-capture, source-of-authority, and neutrality-rule moves
- `Claim-level` and `Pattern-profile`: governing PF overlay and higher-order burden when these change routing or sequencing
- `Structural pattern print`, `Load-bearing node`, and `Collapse radius`: the local belief-machine, the node that keeps regenerating downstream claims, and the dependent claims/routes that must be re-evaluated when it clears
- `Concealment mode` and `DO-orient`: how recognition is being suppressed or how the discourse is socially/affectively stabilized
- `What is withheld and why`, `What remains live`, and `Post-render gate`: held routes, collapse radius, refreshed-state recheck, and the forced re-entry judgment after a load-bearing node is cleared

### Derived Register Formalism Boundary

register-formalism bridge status: the signal-state and derived-register notation is canonical as an
interpretive control bridge over the existing Diagnostic IR. It is not a detached theory annex.
The schema-light register bridge is the current baseline register formalism: schema-light means the registers govern
existing IR/control surfaces when live, not that the registers are optional, future-parity, or a
compact DSL/IR runtime spine. Mandatory `heart` / `xi` / `Omega` / `mu` / `kappa` JSON fields remain a
separate contract migration decision.
`D0` / `D₀` names the surface discourse before diagnostic reduction. `PsiN` / `Ψᴺ` names the
encoded noetic signal-state produced when the diagnostic gate reads that surface through the
available noetic-structure selection space `N_space` / `𝓝`. The live frame `N` is selected or
held from that space as `N in N_space` / `N∈𝓝`; if the input is thin, the selection remains
underdetermined and the case must be held or partialed rather than family-locked.

`PsiN` / `Ψᴺ` is the agent/runtime execution field. When the runtime diagnoses an interlocutor,
it models only a diagnosed interlocutor field `PsiI` / `Ψᴵ` inferred from discourse, profile,
register, response, and source-status evidence. The IR may represent a language-mediated coupling
attempt from `Ψᴺ` toward `Ψᴵ`, but it must not claim access to the interlocutor's soul, total
identity, guaranteed uptake, or agent control of guidance. Reconstruction fidelity must be able
to recover whether the released response addressed the diagnosed interlocutor burden without
turning that diagnosis into a claim of acceptance.

`PsiI` / `Ψᴵ` diagnoses remain uncertainty-bearing. When discourse evidence is thin,
distributed, or compatible with multiple candidate noetic structures, the IR should preserve
alternative reads through `read_status`, `confidence`, `decisive_missing_differentiator`,
`what_remains_live`, or held-route notes rather than family-locking the interlocutor. Default
output need not print a long uncertainty paragraph, but it must not certify interior motive,
soul-state, uptake, or a single interlocutor field where the discourse basis is underdetermined.

Operationally:

```text
D0 -> PsiN<N,m,tau,sigma,H> -> IR(N,m,tau,sigma) -> ∇ route-gradient -> B -> TTP/operator -> R(H,Delta)
```

The Unicode formalism is the theory/spec surface for the same bridge:

```text
𝓝 ⊢ D₀ ⇝ Ψᴺ<N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H>
```

This makes schema-light register bridge real as a derived/conditional runtime bridge: the extra symbols must
govern existing IR formation, owner eligibility, held material, collapse radius, release
posture, or state re-read when live. It still does not make them mandatory JSON/schema fields.

Trace bridge: `field_witness` is required for normal default governed output because Output
Grapher is the graphability/reconstructibility surface for daee-epistemics outputs. It appears as
the final inline sidecar, after Restorative Response, Closing Formulation, and
Closure/Reconstruction Witness, or as an adjacent JSON sidecar when file transport is available.
Only explicit minimal/short/no-graph modes may omit it, and they must say graphing is unsupported
or partial. The sidecar carries a schema-light but machine-checkable trace of route-gradient,
burden delta, field diagnostics, loopbreak, reread, closure, and transfer-boundary evidence. It
does not replace `post_render_gate`, Closure/Reconstruction Witness, Restorative Response, or
Closing Formulation, and does not prove truth, warrant, interlocutor uptake, or full formal
calculus.
When an artifact needs collapse reconstruction, it includes a
`field_witness.coverage_proof` subobject with `initial_burden_set`, `terminal_states`,
`divergence_check`, `curl_check`, and `coverage_complete`. `coverage_complete` is false unless
every initial burden appears in `terminal_states`; positive collapse still requires neutral `∇·B`
and null/resolved `∇×κ` under the scoped closure rule.
Machine-facing `field_witness.terminal_states` and `coverage_proof.terminal_states` are
objects/maps keyed by `B` id, not arrays of terminal objects.

Field-witness reconstructibility addendum: when `field_witness` is present, it must carry
machine-readable `B_LA`, `B_MRP`, `B_total`, burden nodes, generated-by MRP provenance,
dependency edges, held/generated MRP resultants, route-gradient records, roots, parallel groups,
terminal states, schema-light register-delta entries, `∇·` / `∇×` diagnostics, LoopBreak data,
`R(H,Δ)`, owner activation ordering, closure status, `T_lang` boundary, non-claims, and provenance/evidence metadata
sufficient to compare the sidecar against the visible closure witness. Its
`coverage_proof.dependency_graph` records
`nodes`, `edges`, `roots`, `parallel_groups`, and `acyclic`; graph nodes must match the visible
initial-burden / terminal-state accounting. This sidecar is machine-readable reconstructibility,
not a package-bound release-smoke proof and not a truth, warrant, uptake, or formal-calculus
claim.

MRP evidence: `field_witness.reread_pressure` records `TTP-MRP-mid-reread-pressure` when the
post-landed reread state itself is tested. It records
target burden, `R(H,Δ)` delta, pressure activations, active `∇·T` / `∇×T` states, finding,
plain-`∇` route-gradient, route-result type, graph delta, pre-emption basis, route, and non-claims.
It is validated as part of graphability/reconstructibility and does not replace visible MRP in
ordinary compact output.

Formal typing boundary: `∇` is a route-ranking/preorder pressure read over eligible routes,
`LoopBreak(∇×T)` is a partial licensed transition, `R(H,Δ)` rereads held material and the updated
live remainder, and `T_lang: Ψᴺ ⇢ Ψᴵ` is a partial coupling relation rather than an isomorphism,
surjection, or guaranteed update operator on the diagnosed interlocutor field.

The expanded formalism `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` is a theory/specification bridge over this same
Diagnostic IR. It names conditionally live analytic functions; it does not add mandatory schema
fields by itself.

- `♥` names affective-discursive register / release-posture pressure when grief, identity,
  performance, truth-seeking, mixed, or unclear register changes hold/release, tone, sequence,
  owner selection, or final release posture.
- `ξ` names epistemic/warrant grammar when evidence, testimony, authority, proof-method,
  proper function, prima facie status, or defeaters change routing or reread.
- `Ω` names ontological grammar when predication, modality, dependence, causality, being, or
  creator/creation distinction changes the active burden or operator.
- `μ` names meta-noetic memetic vector when carrier, compression, stabilizer, defensive move,
  reproduction, or mutation pattern changes an existing IR field, hold, owner, or reread.
- `κ` names collapse radius / downstream dependency set; `Δκ` names the dependency-radius
  change that the post-render state re-read must consume.

Control-surface test: if a proposed register does not change an existing field, owner/TTP
selection, release permission, collapse radius, held material, `Land(B)`, or `R(H,Delta)`,
it is decorative and must not be promoted into runtime output or schema.

Route-gradient boundary: plain `∇` is a schema-light route-pressure read, not a new IR field. It
may explain why one eligible burden/route is selected next, but only after mandatory diagnostic
reduction, reconstruction, gate checks, routing precedence, and catalogue eligibility have
constrained the live field. It does not replace `Delta`, `del-dot` / `del-cross`, gate checks, or
owner activation rules.

Identity use must be source-status marked in the existing surfaces:

- anchored: public words, explicit self-description, stated framework, explicit affiliation, or
  visible discourse performance
- inference: likely stabilizing role in the noetic equilibrium
- speculative/held: interior motive, sincerity, culpability, soul-state, or primary
  load-bearing status

### Register-To-Owner Handoff Map

The derived registers are owner eligibility aids, not automatic dispatch chains. They help the
IR preserve why an owner may be live while the gate still applies routing precedence,
mixed-case handling, and held-route discipline.

| register | live when | likely owner surfaces | boundary |
|---|---|---|---|
| `heart` | affective-discursive pressure changes tone, amount, hold/release, or closure posture | DW/P7, `output-release.md`, `diagnostic-render-contract.md` | register pressure does not by itself prove deformation or decide content |
| `xi` | warrant, testimony, authority, proof-method, defeater, or proper-function grammar changes the burden | PM/V2, `proof-method-audit.md`, `reason-disambiguation.md` | proof pressure is not automatically an argument dump |
| `Omega` | predication, modality, being, dependence, causality, or creator/creation grammar governs | M9, OQ, DA/DS/HK, V8 | ontology pressure must stay with the smallest owner |
| `mu` | carrier, compression, stabilizer, defense, mutation, or reproduction changes routing or reread | MM / `pattern-profiling.md` | memetic language without control effect is decorative |
| `kappa` | downstream dependency set or collapse radius must be reread after burden landing | `recursive-state-transitions.md`, `routing-precedence.md` | `kappa` is not a TODO list |
| `sigma` | source, label, citation, affiliation, or authority marker changes warrant/source status | AS, `inference-boundary.md`, `nomenclature-normalization.md`, source-status discipline | source label is not operative warrant |
| mixed registers | two or more registers are simultaneously live and compete for release order | `mixed-case-handling.md`, `routing-precedence.md` | preserve composition; do not stack routes automatically |

### Implemented Child-Mode Family Integration

The child-mode tables added through the evidence-gated hardening campaign are integrated into
this noetic-state grammar as parent-owned operator surfaces, not isolated packs:

| family | child modes | parent owner |
|---|---|---|
| M9 semantic/predication | M9-SR, M9-ZM, M9-MQ, M9-LD | `M9-predication-mode.md` |
| PM proof-method | PM-1, PM-2, PM-4, PM-6 | `proof-method-audit.md` |
| AS/source-status | AS-2, AS-3, AS-4, AS-8 | `recursive-state-transitions.md` source-status/noetic-frame discipline |
| DW/doubt ecology | DW-1, DW-2, DW-3, DW-6 | `doubt-vs-skepticism.md` |
| DA/DS/HK | DA-1, DA-2, DS-1, HK-1 | `do-attribute-precision.md` |
| OQ ontological quantization | OQ-5, OQ-6, OQ-8, OQ-9 | `definition-discipline.md` |
| MM carrier/reproduction | MM-2, MM-5, MM-7, MM-8 | `pattern-profiling.md` |

Anti-overclaim guard: child-mode existence is not execution; fixture pass is not live behavior
proof; retained local live samples are not package/release proof; dev-local checker pass is not
universal semantic grading; schema-light register grammar is baseline control, not mandatory hard
field migration.

**Negative rule:** "Meta-noetic memetics" without a control-surface consequence is decorative:
no changed IR/case-state field, no routing suppression, no held material, no collapse radius,
no operator selection, and no state re-read delta. Decorative use is the anti-pattern named in
`references/diagnostics/anti-patterns.md §Higher-Order Vocabulary Theater`.

---

## Gate Protocol - Required Before Module Dispatch

Before any content module is dispatched, the following checks must pass in order. If any check fails, dispatch is blocked; the blocking condition is named explicitly rather than silently resolved.

The IR is formed after diagnostic reduction, not after route selection. The required order is
core axes -> mandatory Phase 2 passes -> triggered overlays / specialty markers -> Diagnostic
IR -> gate checks -> routing precedence -> selected current bounded operation. A route
itinerary is not a valid IR substitute, and `Next move` / `Intervention target` must not be
populated with a chain such as `FPD -> M1 -> DO-8 -> M8 -> restoration`.

After the IR is formed and before routing precedence may dispatch owners, run
`references/diagnostics/ir-reconstruction-pass.md`. The reconstructor receives only the original
input, the populated IR or trace candidate, and reconstruction criteria; it must not reload
`SKILL.md`, the module catalogue, the routing catalogue, owner files, or compiled maps. This is
not a seventh route family. It is a dispatch precondition that checks whether the IR can recover
the live noetic burden, selected operator/TTP, nearest held or deferred alternatives, expected
Land(B), and governance verdict. `reconstruction_fidelity: fail` blocks ordinary module dispatch.
`reconstruction_fidelity: partial` permits only bounded HOLD/PARTIAL output with the reason in
`reconstructor_notes`.

**Gate Check 1 - Mandatory minimum fields populated.**
All pre-dispatch fields in the mandatory minimum, plus any live conditional mandatory fields, must be populated before module dispatch. `Post-render gate` is mandatory for the complete pass record, but it is populated after the bounded restorative move and before closure. Fields that cannot be populated because the basis is too thin route to Stop-4, not to a forced read.

**Gate Check 2 - Consistency rules pass.**
None of the invalid combinations may be present. An IR with an invalid combination is a misread. Re-run Phase 2 before dispatching.

**Gate Check 3 - Routing-precedence suppression rules applied.**
Apply `routing-precedence.md` suppression rules S-1 through S-8. If any suppression rule fires, the routing gate is blocked for the operation that rule suppresses, regardless of how strong the NS or deformation read is.

**Gate Check 4 - P7 stops checked.**
Each P7 stop, when triggered, blocks the corresponding content operation. Check all five stops before dispatch.

**Gate Check 5 - Architectural integrity check.**
The `Restoration target` field must name a specific epistemic layer (`fitrah`, sound reason, authentic transmission, inferential argument) or ontological distinction (`creator-creation`, `transcendence-immanence`, `prophetic-authority`) from `metaphysical-architecture.md`. Also check that no `kernel-thesis.md` violation signature is present.

**Gate Check 6 - Route cleared for content.**
After checks 1-5 pass, confirm the concealment x orientation matrix in `case-state-schema.md`
shows what is deployable now in Layer B. If register-hold applies, the matched content module
is held from direct deployment, not erased from the complete audit record.

Only after all six checks pass does module dispatch proceed.

**Gate trigger tracing:** When any check fires and blocks dispatch, record which check
triggered the block using the `Gate trigger` field in the IR (e.g., `check 3 — S-2`,
`check 4 — Stop-2`, `check 6 — register-hold`). When the gate is `open`, omit the field.
This makes routing failures auditable without re-running the full gate protocol: the IR
record names the blocking check, not just the resulting gate state.

## Runtime Diagnostic Compiler Contract

The skill is a runtime-verifiable diagnostic compiler, not a deterministic argument bank.
Every substantive input case reduces into validated IR before any operator is activated.
The validated IR is the compiler state: it stores the reduced noetic structure, gate status, held
routes, source-status, current restoration target, and the single current bounded operation.

TTP routing proceeds from existing IR fields, not denomination lookup:

```text
IR(pattern_profile, claim_level, reason-category, concealment, deformation, DO-orient)
-> matched TTP/operator
```

Named denomination, school, author, source label, or genealogy may be recorded only as
source-status context when the IR requires it. It is not operative warrant, not public-render
material by default, and not permission to paste a topic-specific argument bank. Default public
source citation is restricted to Qurʾān, Sunnah, and sound Salaf narrations, and each such use
requires a direct source reference.

Compiler lifecycle:

```text
input case
-> diagnostic reduction
-> validated IR
-> reconstruction pass
-> routing precedence
-> selected current live burden
-> TTP entry criteria
-> bounded TTP operation
-> TTP exit criteria
-> burden landing
-> state re-read
-> STOP / HOLD / RECURSE / PARTIAL
```

This lifecycle is runtime-verifiable because each transition has an owner-backed check:
diagnostic reduction must populate the IR before routing; routing precedence may activate
only one current live burden; each TTP must enter through validated IR, not topical association;
each TTP must exit with an operator result; state re-read must re-evaluate held routes and
remaining same-input live burdens before closure or recursion.

TTP activation record is a conceptual audit obligation, not a new IR field. For each active
TTP, the pass must preserve:

```text
entry: validated IR + owner + bounded target + release permission
operation: the owning TTP's specific intervention
exit: result + state delta + held-route recheck
```

If any part is absent, the operator has not executed. Naming M1, M8, M9, FPD, DO-8, or any
other route label is not activation. A route label becomes runtime work only when validated
IR selects it for the current bounded target and the pass records a result that can feed
state re-read.

The compiler must converge through controlled state transitions rather than linear argument
delivery. Convergence means the live same-input noetic structure is restored as far as gates,
stops, release permissions, and response limits permit. It does not mean every detected topic
is answered, nor does it mean the first strong argument licenses STOP.

---

## Render-Mode Policy — IR as Internal State, Not Printout Template

The Full IR Schema below is the **internal state object** for the dispatch gate and governance
pipeline. It governs dispatch, routing, and recursion from inside. It is not a printout template
for the public response.

**Core invariants:**
- Discipline is universal across all modes. Printout is mode-specific.
- Recursive-audit discipline applies in every mode; the full audit printout belongs only to internal/development audit.
- Full recursion in every mode; compact DSL/IR header in default; compact two-ledger witness in
  default hard cases; full raw ledger only in internal/development audit.
- `𝔅_LA (B_LA)`, `𝔅_MRP (B_MRP)`, and `𝔅_total (B_total)` are compact reconstructibility
  witnesses, not the prohibited full raw ledger.

Recursive traversal runs in full in every mode. The mode determines how much diagnostic
machinery is printed, not whether recursion occurs:

```text
/daee-epistemics        = full recursive traversal operationally
                          mandatory compact DSL/IR header
                          prose-first bounded governed Layer B response
                          State/noetic re-read
                          compact ledger witness when burden cycling is live;
                          no full raw ledger / no full Diagnostic IR dump
/daee-epistemics:dsl    = full recursive traversal operationally
                          compact formal Layer A visibility
/daee-epistemics:audit  = deprecated internal/development audit compatibility only
```

**Default mode (`/daee-epistemics`):**

Default Final-Output Preflight Gate (mandatory): before emitting a default answer, scan
the proposed final response. This is the last-mile rewrite gate for the IR owner: forming
the IR is mandatory, but printing the IR is prohibited unless the user invoked `:dsl`,
internal/development audit, or explicitly requested diagnostic trace. If the proposed response contains
prohibited scaffolding, route planning, or meta-composition narration, the response is
invalid and must be rewritten before output.

The Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It also
checks pipeline validity: internal diagnosis -> validated IR -> routed operator selection
-> output-release rubric -> diagnostic-render-contract -> state re-read -> post-render
gate -> STOP / HOLD / RECURSE / PARTIAL decision. Clean prose without pipeline validity is
invalid. The final answer must reflect that Diagnostic IR was formed internally before
routing, that routing came from validated IR, that any TTP was selected as an operator
rather than a prose label, and that output-release and render-contract governance both ran.

Default final-output failure tokens include `## Diagnostic IR`, `[Diagnostic IR]`,
`Case State:`, a full IR/case-state field block, `matched_modules`, `source_basis`, load
ledger, route ledger, planned route list, `Next: FPD -> ...`, strong interior-classification
verdict dumps such as `Concealment: irad primary`, `Deformation: hawa primary`, or
`NS-4/NS-5 compound`, "Now I
have enough", "I now have enough", "I now have sufficient", "Let me compose", "Let me write",
"Let me craft", "Let me construct the diagnostic IR", literal `Recursion decision:`,
`next_eligible_pass:`, and visible `post_render_gate:` fields. Rewrite as clean governed
prose that names only the governing diagnostic fact needed for the answer.

Default recursion must also pass this preflight scan. Bare "Step 1 / Step 2 / Step 3 /
Step 4" or "Move 1 / Move 2 / Move 3" sequencing does not satisfy RECURSE. Same-response
recursion in default mode requires a prose state transition naming what cleared, what remains
live, why the next live burden was already present, and why the next bounded pass is permitted.
If another eligible same-input live burden remains after the current blocker clears, default
output must internally license recursion and continue with one bounded next pass, or render a
partial release-status reason in prose if limits prevent it; silent closure while an eligible
burden remains is invalid.
Use full internal state; render the mandatory fit-for-purpose Layer A compact DSL/IR header
and mode-gated diagnostics. Layer A governs; its full printout is mode-specific.

Default visible frame:

```text
Layer A — Compact DSL/IR header
- read status:
- confidence:
- claim_level:
- pattern_profile:
- reason-category:
- concealment:
- deformation:
- DO-orient:
- live noetic burden:
- initial burden set: [when closure-witness or hard multi-burden accounting is in scope]
- current bounded operator:
- held:
- source-status/noetic-frame:
- decisive missing differentiator: [only when required]
- gate/release decision:

Layer B — bounded governed response
- Hidden Premises
- Burden / Operation N
  - Core Formulation
  - Bounded Response / operative submoves
- TTP/operator trace when a named operator does runtime work

State/noetic re-read

Restorative Response
Closing Formulation
```

This is a compact DSL/IR printout, not a full raw IR dump. The visible fields above are
render-time aliases of existing IR, case-state, source-status, and output-governance fields;
they add no new IR fields. Default still suppresses `matched_modules`, route ledger, full
Case State, and the raw `[Diagnostic IR]` block.

Submove-vs-recursion rule:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
Gloss: hiddenness, punishment/accountability, source-status, source-worldview, and
identity-stabilization can be operative submoves under one governing burden only when the
same-function gate holds; they become separate burden-cycles after `Land(B) -> R` licenses a
genuinely new input-anchored `B`. Hard compound inputs must not collapse distinct
accountability, hiddenness/coercive-guidance, punishment/mercy, source-worldview, predication,
testimony, grief/register, or family-local proof-method pressure into one umbrella burden.
Notation owner: `recursive-state-transitions.md`.

*Prohibited in default mode — must not appear in the public response:*
- The `## Diagnostic IR` section header.
- The code-fenced `[Diagnostic IR]` block.
- A full `[Case State]` block with all IR fields populated.
- A Load Ledger or bundle resolution table.
- A Render Permission Check or full source-basis printout.
- A bibliography, "Primary Sources Referenced", external research-style source list, or
  source-basis ledger unless the user requested sources/citations or the task is
  internal/development audit or research.
- The full procedural audit template.
These items are prohibited regardless of case complexity. Plain `/daee-epistemics` does not become
Level 2 or Level 3 merely because the case has multiple live burdens.

*Default compact DSL/IR header — mandatory in default mode:*
Default Layer A surfaces only the compact compiler trace: read status, confidence,
claim_level, pattern_profile, reason-category, concealment, deformation, DO-orient,
live noetic burden, current bounded operator, held, source-status/noetic-frame,
gate/release decision, and decisive missing differentiator when required. It must not
leak verbose DSL/audit machinery; use
`references/rubrics/diagnostic-render-contract.md` for the canonical frame and contrast pairs.

*Recursion in default mode:*
Full recursive traversal runs. The traversal must be visible through the compact DSL/IR
header and state-transition progression, not through printed gate machinery. The response
progresses through live burdens before final synthesis:

```text
bounded move → state re-read: what cleared → what remains live
→ next eligible burden → decision → next bounded move (if eligible)
```

Literal `Recursion decision:`, `next_eligible_pass:`, `Governance:`, or visible
STOP / HOLD / RECURSE / PARTIAL governance labels must not appear in default output. They
belong to `:dsl`, internal/development audit, pass-review, or diagnostic trace. In default
mode, continuation appears as a prose transition plus one bounded next pass, not as a state label.

Numbered essay headings do not substitute for this progression. "Move 1 / Move 2 /
Move 3" is not a post-render gate unless the response also shows, in ordinary prose,
what cleared, what remains live, why the next live burden was already present, and why the
next bounded pass is eligible.

TTP activation must be source-backed and operational. A label such as "the M1 move" or
"the M8 move" is not enough: the TTP must be selected by the validated IR, assigned a
bounded target, used to perform its operation, and followed by state re-read before any
downstream TTP releases.

**DSL mode (`/daee-epistemics:dsl`):**
- Full recursive traversal runs operationally.
- A compressed Case State block or selected IR fields may be shown using the Level 2
  shape from `diagnostic-render-contract.md`.
- The full code-fenced `[Diagnostic IR]` schema block does not appear even in DSL mode.
- Do not show the full load ledger, full source-basis table, or full routing-gate section
  unless the task explicitly escalates to internal/development audit.
- Use original module IDs in any visible `matched_modules`; never use omnibus filenames.

**Internal/development audit compatibility (`/daee-epistemics:audit`):**
- Deprecated as a public render mode; do not rely on it for default governance visibility.
- Full recursive traversal runs operationally.
- The fuller IR governance state may be surfaced as a structured block.
- Populate only fields with operative content; do not dump the full schema template.
- Runtime/bundle ledger, when shown, must resolve atomized paths through
  `compiled-module-map.json`; do not list missing atomized files as literal load targets.

---

## Full IR Schema

Render-mode scope: this template is an internal control shape and may be visible only in
`:dsl`, internal/development audit, pass-review, or diagnostic trace. It is not a default output template.
Visible block format is internal/development audit / diagnostic-trace only for the post-render gate fields below.
In default mode this gate runs internally and renders only as prose transition or prose
closure/hold/partial wording when needed.

```text
[Diagnostic IR]

--- Workflow Layer ---
Case family:
Claim-type:                          # logical | metaphysical | moral | historical | transmission | phenomenological | authority
Claim-level:                        # first-order | meta-epistemic | meta-ontological | meta-noetic | cross-level
Pattern-profile:                    # PF-1 ... PF-12 | none
NS code:                             # NS-1 through NS-12, or provisional
Deformation:                         # primary [| secondary], in intervention order
Concealment mode:                    # clear | irad | juhud | inkar | istikbar | nifaq | mode-? | compound
DO-orient:                           # truth-seek | identity-perf | autotelic | zann-mode | mixed
RT marker (if active):               # RT-1 | RT-2 | RT-3 | RT-4 | none; keep `none` for ḥadīth-authentication cases unless a separate Qurʾānic RT family is also live
Read status:                         # dominant | distributed | underdetermined
Confidence:                          # strong | provisional | low
Alignment state:                     # blocked | tribunal-loosened | frame-cleared | recognition-surfaced | alignment-advanced
Recognition strength:                # none | weak | medium | strong
Continuation eligibility:            # not-assessed | blocked | eligible-on-refresh
P7 stops active:                     # Stop-1 | Stop-2 | Stop-3 | Stop-4 | Stop-5 | none
Routing gate:                        # open | V2-required | deformation-first | semantic-discipline-required | register-hold | stop-condition
Gate trigger:                        # omit when gate is open; when gate fires: check [1–6] + rule or stop id, e.g. "check 3 — S-2" or "check 4 — Stop-2"
Matched modules:                     # current-pass, case-state-justified coordination only
Prohibited moves:                    # list any PM from routing-precedence or do-attribute-precision

--- Architectural Layer ---
Reason-category:                     # 1 (sound) | 2 (corrupted) | 3 (pseudo-neutral) | 4 (inherited)
Backbone predicates active:          # list true predicates from arabic-backbone-predicates.md
Foreign premise:                     # detected [premise, source, functional role] | none-detected | uncertain
Upstream findings:                   # criterion-import | tribunal-installation | transmission-demotion | semantic-neutralization-recontenting | semantic-neutralization-evacuation | lexical-ontological-trap
Philosophical usurpation:            # type [A | B | C | D] + active telltale features | none
Architectural layer disrupted:       # fitrah | sound-reason | authentic-transmission | inferential-route | transcendence-immanence | prophetic-authority | none
Ontological disorder:                # category-mistake | illicit-analogy | equivocal-predication | composition-panic | person-multiplicity-conflation | perfect-being-usurpation | none
Restoration target:                  # what noetic faculty, epistemic ordering, or ontological distinction is being cleared or re-established
Structural pattern print:            # optional; compact local pattern description when PF code alone would lose practical framing
Load-bearing node:                   # optional; criterion, authority rule, semantic hinge, category-set, or noetic blocker currently carrying the pressure
Collapse radius:                     # optional; downstream claims/routes that depend on the load-bearing node and must be re-evaluated when it clears
Intervention target:                 # optional; the bounded operation that clears the load-bearing node
Framing notes:                       # optional; internal renderer constraints preventing citation dump, argument bank, or wrong-family release
Reconstruction fidelity:             # pass | partial | fail; internal/trace field from ir-reconstruction-pass.md
Reconstructor notes:                  # required when reconstruction_fidelity is partial/fail; compact neighbor contrast when useful

--- Output Governance ---
                                  # Canonical internal/audit diagnostic record and Layer B definition:
                                  # `SKILL.md §V.A — Two-Layer Output Contract`.
                                  # Output-governance fields govern deployable Layer B. They do not
                                  # define or expand the default visible Layer A surface.
                                  # The complete diagnostic record is retained internally
                                  # for audit-capable render modes.
                                  # Default visible Layer A is the compact fit-for-purpose surface
                                  # governed by `diagnostic-render-contract.md`.
Source basis:                        # anchored | synthesis | inference | speculative - per claim
Inference boundary active:           # yes | no
Deployable Layer B output shape:     # content | relational | maieutic | invitational | single-response | held-pending
Next move:                           # one specific action the response takes next
What is withheld and why:            # Layer B hold only; never used to omit the internal/audit diagnosis or matched modules
What remains live:                   # open differentiators, unresolved axes, or questions the next exchange must answer
Post-render gate:                    # mandatory state re-read / Re-Entry Gate before STOP, HOLD, RECURSE, or PARTIAL
  Cleared this pass:
  Remaining live distortions:
  Held routes rechecked:
  Newly released routes:
  Next eligible pass:
  Recursion decision:                 # STOP | HOLD | RECURSE | PARTIAL
```

For `/daee-epistemics:dsl` or internal/development audit render, a burden-cycle may be compactly surfaced as:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded move:
state re-read:
Release status: prose closure/hold/partial/continuation status; no literal STOP/HOLD/RECURSE/PARTIAL label
```

This is a DSL/audit shape, not a normal-answer ledger. Ordinary default answers may compress it,
but the fields remain the internal state re-read contract.

---

## Field Rules

Compression rule: the IR is not a checklist to be filled performatively. Populate only fields with operative content, except for mandatory control fields such as `post_render_gate`, which must record the governance decision even when its result is `none` / STOP.

Noetic-object rule: populate the IR as a state of the structure, not as a paraphrase of the
discourse. The point is to formalize what configuration is live, what governs release now, and
what depends on what - not merely to restate the surface wording. When a meta-noetic memetic
read is live, formalize the governing epistemic rule, linguistic pattern, load-bearing node, and
collapse radius through existing fields rather than inventing a new route or field.

Concealment mode is mandatory. Use `clear` when no active concealment mode is positively read.
Use `mode-?` when the axis remains unresolved. Blank values, em dashes, or placeholders such as
`none confirmed` are invalid because they erase the difference between "resolved absent" and
"still unread."
`clear` is a positive non-operative finding, not a synonym for "the speaker stated the claim
openly." When a compact Layer A read simultaneously marks an imported framework, pseudo-neutral
tribunal, or identity-stabilizing reading lens as operative, do not render `concealment: None
detected` and do not use `clear` unless the framework has been positively exposed and no longer
governs the present pass. If the surface claim is open but the governing lens is unacknowledged,
record a non-clear mode where readable, or `mode-?` with an anchored note such as
`surface-open / framework-concealed`.
Concealment mode is control-bearing: framework-concealment normally registers as `ξ` pressure
when a proof/warrant/source rule is presented as neutral, as `Ω` pressure when source-order or
ontological predication is covered, as `κ` pressure when the proof-stack loops back to the same
unexamined lens, and as `∇·B` pressure when the covering keeps a burden live. Do not add a new
person-level judgment from those symbols; use them to govern hold/release, MRP pressure, and
restoration target.

**Mandatory minimum**

For any substantive response claiming to have done V1, the following fields must be populated:

- Case family
- Claim-type
- Deformation
- Concealment mode
- DO-orient
- Read status
- Confidence
- Alignment state
- Recognition strength
- Continuation eligibility
- P7 stops active
- Reason-category
- Routing gate
- Matched modules
- Restoration target
- Next move
- Output shape
- Post-render gate
- Claim-level
- Pattern-profile

`Post-render gate` is mandatory for a completed pass, not for initial dispatch. It is populated
after the bounded move and before STOP, HOLD, RECURSE, or PARTIAL is declared.
`Reconstruction fidelity` is mandatory before ordinary module dispatch in new release-grade
trace/verdict evidence. It is schema-optional only so legacy smoke artifacts remain readable.

If these fields cannot be populated because the basis is too thin, the correct output is Stop-4 plus the specific missing differentiator.

**Conditional mandatory additions**

Populate these whenever their trigger is live:

- Internal IR discipline: in the validator-backed Diagnostic IR, `Claim-level` and `Pattern-profile` stay explicit even in routine cases. Use `Claim-level: first-order` and `Pattern-profile: none` when the higher-order and PF triggers have been checked and found inactive. Compression to omission is only for surfaced routine case-state, not for the internal IR.
- `Foreign premise` and `Upstream findings` when criterion import, tribunal installation, transmission demotion, or framework import is visible
- `Backbone predicates active` when trigger mapping in `references/diagnostics/arabic-backbone-predicates.md` calls for checks
- `Philosophical usurpation` when an imported framework is functioning as upstream tribunal
- `RT marker` when the live transmission pressure instantiates RT-1 through RT-4. Ḥadīth-authentication cases without a separate Qurʾānic RT family keep `RT marker: none` and route through `references/diagnostics/hadith-authentication-epistemology.md`
- `What is withheld and why` when register-hold, semantic gate, or stop governance keeps a diagnosed downstream route from current deployment
- `What remains live` when live alternatives, held routes, a boundary-reset condition, or a load-bearing dependency with downstream collapse radius must stay visible
- `Alignment state`, `Recognition strength`, and `Continuation eligibility` whenever restoration progress, stop thresholds, or refreshed continuation are doing real routing work. In the validator-backed internal IR these fields should be explicit whenever a landed move, recognition judgment, or recurse-vs-stop decision is live.
- `Post-render gate` after every bounded restorative move and before any closing decision. It is mandatory even when the decision is STOP; STOP is invalid unless the gate has run.
- `Reconstruction fidelity` after initial IR formation and before routing precedence. `partial` or `fail` requires `Reconstructor notes`; `partial` permits only bounded HOLD/PARTIAL output, and `fail` blocks ordinary module dispatch.
- `Decisive missing differentiator` is conditional-mandatory whenever `Confidence` is anything other than `strong` *or* `Read status` is anything other than `dominant`. The field names the one signal that would refine, falsify, or collapse the remaining ambiguity in the read. This is a falsifiability anchor against cosmetic IR formation: a paraphrase of the input cannot fill it without exposing itself, while a structural read can. The field comes from `references/diagnostics/case-state-schema.md §Decisive missing differentiator`; this rule promotes it from optional to conditional-mandatory inside the validator-backed internal IR. If the basis is too thin to name a differentiating signal at all, the correct output is Stop-4, not a forced read.

**Optional structural framing fields**

The fields `Structural pattern print`, `Load-bearing node`, `Collapse radius`,
`Intervention target`, and `Framing notes` are optional IR fields. They do not add a
new routing pass and do not replace `claim_level`, `pattern_profile`, NS/DO/RT routing,
FPD, V2, M9, V10, P7, or routing-precedence suppression. They are a local descriptive
layer used only when the existing fields would otherwise lose the practical framing that
controls sequencing and release.

Populate them only when all of the following hold:

- `Claim-level` is `meta-epistemic`, `meta-ontological`, `meta-noetic`, or `cross-level`.
- The input is thick enough to identify a real structure rather than a topic label.
- The pattern changes routing, sequencing, suppression, release discipline, or renderer constraints.
- PF code alone is too coarse to preserve the local load-bearing node and what is held behind it.

Do not populate them on thin input, as decorative terminology, as public-output boilerplate,
or as a substitute for module ownership. `Structural pattern print` names the practical
shape; `Load-bearing node` names what must clear first; `Collapse radius` names what
depends on that node; `Intervention target` names the next bounded clearing operation;
`Framing notes` tells the renderer how not to mishandle the case.

Typical framing notes are prohibitions, not miniature arguments:

```text
do not answer as fiqh detail until imported criterion is exposed
do not use external scripture as a clean independent foundation
do not treat Arya Samaj as Advaita
do not treat anatta as simple materialism
do not debate kashf occurrence before jurisdiction is classified
do not collapse abuse wound into doctrine
avoid citation bank; use source-use discipline only if prooftexts become live
```

These notes are internal constraints. They appear in public output only when the render
contract permits a diagnostic or audit-style response.

**Current-pass activation rule**

- `Matched modules` records only the case-state-justified coordination active in the present pass.
- Diagnosed downstream content that is held by register, semantic, or stop governance remains explicit in Layer A through `What is withheld and why` / `What remains live`; it is not silently dropped, but it is also not treated as simultaneously active.
- **Three-way activation partition:** Absence from both `Matched modules` and `What is withheld and why` means the module was never triggered by the current case-state — it is not in scope given the diagnostic read. Presence in `What is withheld and why` alone means the module was triggered but blocked by governance. Presence in `Matched modules` means the module is active in this pass. These three states must not be collapsed; an auditor must be able to distinguish "never in scope" from "triggered and suppressed" without re-running the diagnostic gate.
- **Ghost-load prohibition:** A `matched_modules` entry without a corresponding `source_basis` entry with `source_kind: "module"` and `module_id` matching the entry's `id` is a ghost-load: the source file or compiled runtime section was loaded but did not demonstrably govern any output claim or routing decision in this pass. Ghost-loads are gate-integrity failures equivalent to fabricated activation and must be corrected before dispatch — either by adding the missing `source_basis` entry (naming the specific claim or routing fork the module governed) or by moving the module from `matched_modules` to `What is withheld and why` with an explicit reason.
- Schema note: `source_basis` is not an unconditional top-level required field for bare schema compatibility, but it is conditionally required whenever `matched_modules` is present and non-empty. Executable catalogue/source-basis coverage is enforced by `tools/check_ir_instance_integrity.py`.
- **Reconstruction prohibition:** A `matched_modules` entry that cannot be reconstructed from the input burden through existing IR fields is label-only or topic-only routing even when its owner file exists. Correct by re-running diagnostic reduction, moving the owner to `What is withheld and why`, or emitting bounded HOLD/PARTIAL with `reconstruction_fidelity: partial/fail`.
- `Next move` names one live move only. It is not a queue of later modules.
- `Intervention target` and `Next move` name one burden-level function. They do not name a route
  chain, module itinerary, or list of internal TTP labels. Acceptable shape: `imported-criterion
  tribunal test` or `worship-worthiness criterion test`. Invalid shape: `FPD -> M1 -> DO-8 ->
  M8 -> restoration`.
- When several TTPs are required to land that one live burden, record them internally as
  operative submoves, each with target -> operation -> result. They remain under the same
  current-pass activation until the burden landing is reached and state re-read runs.
- Before dispatching several owner/TTP submoves for one burden, emit a deterministic owner
  activation plan in the IR/control surface with
  `policy_id: "diagnostic-ir-pressure-owner-floor-v1"`. The plan is produced before Layer B:
  first freeze the baseline burden decomposition from stable pressure classes, then select required
  owner families from the pressure-owner floor, and only then render `Matched owner/TTP route`, ACT
  records, and Layer B submoves. The stable owner floor is:
  source/criterion/authority gates before downstream content owners; Trinitarian
  model/person-language identification before definition, predication, or consequence work;
  definition/meaning -> M7; predication/category/person-nature transfer -> M9;
  entailment/consequence/backread -> M8; source/proof-text/warrant/hidden support ->
  source-status/authority-order repair; scope/stop/bounded-reply/closure-immunity -> P7 after
  load-bearing owners unless P7 is the active stop owner. P1/restoration, tone, closing
  formulation, broader source reminders, and pastoral reorientation are
  `optional_non_load_bearing` unless the burden target itself is restoration/orientation. The plan
  records `required_before` for sequenced owners, `parallel` groups for order-independent
  load-bearing owners, `contingent` owners with their trigger, `optional_non_load_bearing` owners
  for restorative or tone-only support, and `hold_partial` for owner work that remains unresolved.
  It governs `Matched owner/TTP route`, ACT record order, Layer B submove order, and
  `field_witness.owner_activation_ordering`. Optional or held owners do not change the canonical
  required activation fingerprint. `required_before` entries are owner-family objects with
  `target`, `before_owner`, and `after_owner`; arrays, body-ref pairs, and burden-event pairs are
  not valid ordering rules. `parallel_groups[]` plan entries use `target`, `group`, and `owners`;
  only the per-activation mirror rows use `ordering_group`. A parallel group is only for two or
  more distinct owner families whose load-bearing operations are order-independent on the same
  target. Do not mark duplicate ACT rows from the same owner family as `parallel`, and do not list
  one owner twice or alone in `parallel_groups[].owners`; either sequence the same-owner work as
  `required` in stable ACT order or collapse it into one owner activation when one operation lands
  both pressures.
  - Science-only/source-totalization rule: if the input says scientific explanation, empirical
    method, or scientific authority is the only knowledge source/criterion, the source-order gate is
    structurally live. Execute `source-status-repair.source-order` before
    `M1.self-grounding-test` on the same burden and record
    `required_before: source-status-repair -> M1`, unless Layer A explicitly proves source-order
    non-load-bearing with a reason. For that science-only source-order canary, use exact pressure
    labels: `scientific-explanations-only-knowledge-source` for the source-status ACT and
    `only-science-counts-standard` for the M1 ACT. Use simple terminal-state maps in machine
    fields: `"terminal_states": {"B1": "landed"}` in both `field_witness` and `coverage_proof`.
    Use the exact Layer A concealment boundary
    `Concealment mode: sincere clarification/shubhah pressure path; boundary: diagnostic noetic covering only; no hidden soul-state or takfir judgment.`
    Do not label this narrow frame `mixed` unless at least two dominant source-owned refusal
    components are explicitly diagnosed and named.
  - Register-derived burden floor: before owner-plan emission, derive `B_LA` structure from the live
  register set in `IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)`, not from a named case template:
  `burden_floor = {B_r : r in live_registers(IR(...))}`. `Omega` live requires an
  ontological/predication burden; `xi` live requires a warrant/authority burden; `mu` live requires
  a memetic-carrier decomposition burden; `kappa` live requires a dependency/collapse burden; and
  `heart` live requires an affective/posture burden. A burden may be multi-typed, so the
  requirement is coverage per live register, not one burden per register. The selected N-frame
  supplies the burden labels and content; register liveness supplies the floor structure.
  - Academic-prestige/source-order shubhah canary: when the mixed field contains an
    academic-prestige, science-authority, or secular-ethics public-knowledge tribunal plus Muslim
    identity/social-respectability pressure and sincere shubhah, the stable N-frame token is
    `mixed-academic-source-order-shubhah`; do not alternate to
    `mixed-academic-public-knowledge-shubhah`, `mixed-academic-respectability-shubhah`, or
    `mixed-academic-secular-identity-shubhah`. Identity/social-respectability is a pressure inside
    that frame unless the input makes it a separate source-owned baseline burden. The pressure-class
    structure is stable: B1 imported public-knowledge tribunal/carrier -> FPD; B2 source-order
    status -> source-status-repair; B3 reason/revelation-order -> P3; B4 sincere shubhah boundary
    -> doubt-vs-skepticism before P1; generated B5 bounded-answer/source-order recoil ->
    source-status-repair before P7. The exact pressure labels are B1/FPD
    `academic-prestige-science-secular-ethics-hidden-tribunal`, B2/source-status
    `science-secular-ethics-only-public-knowledge-source`, B3/P3
    `revelation-authority-as-anti-intellectual-betrayal`, B4/doubt-vs-skepticism
    `sincere-doubt-vs-academic-respectability-shield`, B4/P1
    `salah-tawhid-attraction-restoration`, B5/source-status
    `source-order-recoil-hidden-support`, and B5/P7 `bounded-answer-reopen-boundary`.
    Any `required_before` edge must reference owners that actually execute on the same target. Do
    not emit `source-status-repair -> P3` on B2 unless P3 has an ACT row on B2; in this canary frame
    P3 belongs to B3. Use `P1.restoration` consistently, not a drifting `fitrah-restoration`
    operation token, unless a future source-owned vocabulary migration changes the operation name.
    Generated B5 source-order recoil uses `hidden-support-blocked`; reserve
    `hidden-authority-source-status-bounded` for hidden authority/source-status transfer, not
    post-restoration source-order recoil.
- When normal governed output emits `field_witness`, also emit
  `field_witness.normalized_activation_record`. This is the schema-light structural comparison record:
  `n_frame`, `live_registers`, `burden_floor`, and `per_burden[]` with `burden_id`, `owner_id`,
  `operation`, `delta_result`, `mrp_route_result_type`, `terminal_state`, and
  `generation_depth`. It is generated after the owner plan and burden traversal are fixed, and
  it must be derived from `owner_activations[]`, `mrp_resultants[]`, terminal states,
  generated-burden depth, and the burden ledgers rather than authored as a separate proof claim.
  `burden_floor` is a string list of B IDs only, not register/object rows. `per_burden[]` is
  ACT-level despite its historical name: emit one row for every visible ACT /
    `field_witness.owner_activations[]` object, including multiple rows with the same `burden_id`
    when several owners land one burden. When `live_registers` is claimed in NAR, the compact Layer A
    header must include an explicit `live registers: [...]` line with the same set. `n_frame` is a
    stable kebab-case frame token selected by Diagnostic IR, not prose. For the narrow science-only
    source-order warrant frame, use exactly `science-only-source-order-warrant`. In NAR,
    `delta_result` is the suffix token only, such as `science-source-bounded` or
    `self-authorizing-standard-invalidated`; do not include `Delta(B1):`, `Δ¹B:`, or any other
    burden-local prefix in `normalized_activation_record.per_burden[].delta_result`. Canonical
    owner-local suffixes are source-owned in
    `references/diagnostics/delta-result-vocabulary.json`
    (`diagnostic-ir-delta-result-vocabulary-v1`). Governed ACT and NAR emission must use those
    tokens by construction for listed owner families; post-render checkers reject drift but are not
    the source of the vocabulary.
- For explicit A.13 hard-register IR artifacts only
  (`diagnostic_ir_schema_version = "0.4.3-hard-registers-v1"`), the hard-register live/held set
  must reconcile with `field_witness.normalized_activation_record.live_registers`, live hard
  registers named in `field_witness.register_deltas`, and
  `field_witness.coverage_proof.diagnostic_completeness`. The canonical hard-register keys remain
  `heart`, `xi`, `Omega`, `mu`, and `kappa`; `sigma` stays source-status/source-basis evidence and
  is not a sixth hard-register key. This is a version-gated checker/fixture contract and does not
  require schema-light governed outputs to emit hard-register fields by default.
- A.13.3.1 opt-in emission surface: a governed artifact MAY emit
  `field_witness.canonical_ir_projection` only when the hard-register version is explicitly
  selected. The projection carries `schema: "b5-canonical-ir-projection-v1"`,
  `diagnostic_ir_schema_version: "0.4.3-hard-registers-v1"`, `hard_registers`, and mirrors of
  NAR/diagnostic-completeness fields. It must reconcile with root hard registers, NAR live
  registers, register deltas, and diagnostic completeness; `sigma` remains outside the
  hard-register object. This projection is machine-facing opt-in evidence, not public prose, not
  default always-on runtime output, not full IR decode, and not proof of interlocutor uptake. It
  never replaces the visible opening noetic-field banner or the compact Layer A / Diagnostic IR
  header; those remain the human-facing field read and compliance surface.
- B.5.2 opt-in decode object: a projection-bearing artifact MAY also emit
  `field_witness.canonical_ir_projection.decoded_ir` with
  `schema: "b5-canonical-ir-decode-v1"`. This object is a checker-owned
  reconstruction surface from visible ACT rows plus `field_witness.owner_activations`,
  `normalized_activation_record`, and `canonical_ir_projection`; it is not a free-standing
  natural-language parser. It repeats the recoverable IR-like slots (`n_frame`,
  `live_registers`, `burden_floor`, `diagnostic_completeness`, optional `hard_registers`,
  optional `register_composition`, and `per_burden[]` rows with `owner_id`, `operation`,
  `pressure`, `body_ref`, `delta_result`, `mrp_route_result_type`, `terminal_state`, and
  `generation_depth`) so a checker can prove the decode agrees with visible ACT/body evidence
  and machine field-witness evidence. Schema-light projections may use `decoded_ir` without
  hard-register fields; hard-register projections must keep decoded hard registers equal to the
  projection. This remains an opt-in B.5 scaffold and does not claim arbitrary full IR decode,
  runtime/default hard-register emission, guaranteed uptake, or package/provenance proof.
- B.5 full-IR decode scaffold: a projection-bearing artifact MAY additionally emit
  `field_witness.canonical_ir_projection.full_ir_decode` with
  `schema: "b5-full-ir-decode-v1"`. This object is still opt-in and checker-owned, but it is
  stronger than `decoded_ir`: it reconciles the decoded rows with `B_LA`, `B_MRP`, `B_total`,
  `coverage_proof.dependency_graph`, terminal states, generated-burden provenance, formal
  reread state, escape-route accounting, terminal `no_new_resultant_proof`, and source/sigma
  boundary evidence where those fields are present. It is a field-witness-equivalent projection
  scaffold, not a standalone natural-language parser, not default hard-register emission, not a
  package/provenance claim, and not guaranteed `T_lang` uptake.
- Trinitarian John 17:3 owner-plan canary: the John 17:3 case is an instance of the
  register-derived rule, not a runtime template. When its N-frame makes `Omega`, `xi`, `mu`, and
  `kappa` live through the quoted reply's person/nature model transfer, proof-stack support,
  model-carrier compression, and eternal-life/sent-one entailment, `B_LA` must cover those register
  types before any generated MRP burden. The canary may expect stable labels such as
  `trinitarian-person-nature-model-transfer`, `john-1-1-and-1-john-5-20-proof-stack`, and
  `eternal-life-knowing-jesus-entailment`, but those labels are supplied by the Trinitarian N-frame
  after live-register derivation. Boundary, doctrine-immunity, proof-carousel, or bounded-reply
  recoil remains post-land/generated unless the input asserts it as an independent baseline claim.
- For that Trinitarian canary instance, the deterministic owner plan does not use
  `parallel_groups`; it emits required owner rows and required-before edges for the register-typed
  burdens. These exact labels are canary expectations for the Trinitarian N-frame, not a general
  B1-B5 floor template: B1 `do-christian-extensions.model-identification` /
  `trinitarian-person-nature-model-transfer` before M9 / `father-only-true-god-predicate-transfer`;
  B2 M7 / `only-placement-analogy` before M9 / `2-plus-2-predicate-category`; B3
  `source-status-repair.source-order` / `john-1-1-and-1-john-5-20-proof-stack` before
  `authority-order-repair.authority-order` / `proof-text-hidden-support`; B4 M8 /
  `eternal-life-knowing-jesus-entailment` before M9 / `sender-sent-relation-category`; generated B5
  P7 / `sacred-doctrine-bounded-reply-immunity` before `source-status-repair.source-order` /
  `full-system-doctrine-hidden-support`.
- When a load-bearing premise, criterion, or authority node has been cleared, `What remains live`
  should mark any dependent claims whose support has collapsed or whose status now requires
  re-evaluation before further routing.
- When Stop-2 fires or a move has landed, boundary reset applies: later activation begins from a fresh V1-governed round rather than from carried-forward module state. A fresh round may be opened by a later reply or by a clear differentiating signal within the same message, its accompanying propositions, or its entailments, but only when the refreshed state still shows an unmet restoration target and no stop, register-hold, or semantic gate bars the next move.

**Post-render state re-read / Re-Entry Gate**

After every bounded restorative move, and before any closing or STOP decision, the IR must run
`post_render_gate`. The gate asks:

1. What was cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. Where does the refreshed route-gradient `∇` point: held burden, generated burden, hold,
   loopbreak, or none?
6. Is there a next eligible pass?
7. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

Decision semantics:

- `STOP` is valid only if the gate has run, no live distortion remains, no held route has become
  newly eligible, no route-gradient points toward an input-anchored burden in licensed scope, and
  `next_eligible_pass` explicitly records `none`.
- `HOLD` is valid only when remaining material exists but its release signal is absent because a stop, register-hold, semantic gate, thin-basis rule, or other hard rail still blocks it.
- `RECURSE` is required when another live distortion remains in the same input, or when a held route becomes newly eligible after the current pass clears its blocker.
- `PARTIAL` is required when token, tool, or interaction limits prevent completion while recursive pressure remains. Do not emit a false STOP in that condition.

Core recursive traversal rule: no premature STOP while an eligible live burden remains. After every
bounded restorative move, run state re-read. STOP is valid only when the current governing blocker
has been addressed, no eligible live burden already present in the original input remains live, no
held route became releasable after the move, continuing would be argument-stacking rather than
governed traversal, and P7 permits stopping. If another eligible live burden remains in the same
input, choose RECURSE or PARTIAL, not STOP. HOLD is valid only when the remaining burden needs an
absent release signal not present in the input.

Recursion is not argument dump. It releases one live burden per burden-cycle, upstream before downstream, with
matched modules reset and re-derived from the refreshed state after each bounded move.

The gate is not a new routing pass. It is the post-render enforcement point that makes the
validated IR remain live after the response has made its bounded move.

**Recursive-state model:** `references/diagnostics/recursive-state-transitions.md` is the canonical abstract owner of the STOP / HOLD / RECURSE / PARTIAL state model. The fields `continuation_eligibility`, `alignment_state`, `recognition_strength`, and `post_render_gate` are this IR's typed carriers of that model. State-transition semantics and recursive re-entry conditions are defined in `recursive-state-transitions.md`; this section governs only how those states are represented in the IR record.

**State-carry partition:** The consolidated table of what state re-read retains, resets, and re-evaluates across a pass boundary is in `references/diagnostics/recursive-state-transitions.md §State Carry / Reset / Re-Evaluation Table`. The boundary-reset rule for matched modules after Stop-2 and the current-pass activation rule above are prose expressions of that same partition.

**Acceptance-state rules**

- `Alignment state` keeps restoration progress typed. Use `blocked` when the governing filter still controls the case; `tribunal-loosened` when the imported criterion has visibly lost its neutrality claim; `frame-cleared` when the subject can now examine signs, revelation, or transmission without the old filter governing; `recognition-surfaced` when a landed move has produced medium or strong visible uptake; `alignment-advanced` only when positive recognition and willingness to inhabit the restored order are visibly present.
- `Recognition strength` must track the stop threshold rather than tone alone. `weak` covers politeness, irritation, surprise, silence, or rhetorical concession without state-shift; `medium` covers local consequence admission, reflective pause, or premise-examination; `strong` covers explicit blocker removal, accurate restatement, sincere next-questioning from the cleared frame, or a visible register shift into inquiry.
- `Continuation eligibility` governs post-landing release. Use `not-assessed` before the question is live; `blocked` when a stop, hold, gate, or satisfied target forbids more release; `eligible-on-refresh` only when a fresh differentiating signal has reopened V1, the restoration target remains unmet, and no stop, register-hold, or semantic gate remains live for the next move.

  **Positive termination:** When the restoration target is met and `alignment_state` is
  `alignment-advanced` with `recognition_strength: strong`, set
  `continuation_eligibility: blocked` and record `What remains live: none — restoration
  target satisfied`. This sub-type of `blocked` marks restorative completion, not a
  governance stop. It must be distinguished from `blocked` under an active stop condition
  so that audits can confirm the framework terminated correctly rather than prematurely.

**State transition table** — the three acceptance-state fields interact as follows. This
table makes the forward direction explicit: given alignment state and recognition strength,
what does continuation eligibility resolve to? Derived from the prose rules above; does not
introduce new semantics.

| `alignment_state` | `recognition_strength` | → `continuation_eligibility` |
|-------------------|------------------------|------------------------------|
| `blocked` | any | `blocked` |
| `tribunal-loosened` | `weak` or `medium` | `blocked` |
| `tribunal-loosened` | `strong` | `eligible-on-refresh` (if target unmet); `blocked — satisfied` (if target met) |
| `frame-cleared` | `weak` | `blocked` |
| `frame-cleared` | `medium` | `eligible-on-refresh` (if target unmet); `blocked` (if no fresh signal yet) |
| `frame-cleared` | `strong` | `eligible-on-refresh` (if target unmet); `blocked — satisfied` (if target met) |
| `recognition-surfaced` | `medium` or `strong` | `eligible-on-refresh` (if target unmet) |
| `recognition-surfaced` | `weak` | `blocked` |
| `alignment-advanced` | `strong` | `blocked — satisfied` |

All `eligible-on-refresh` outcomes additionally require: a fresh differentiating signal has
reopened V1, and no active stop, register-hold, or semantic gate remains live for the next
move.

**Consistency rules**

The following inconsistencies are invalid:

- `Read status: underdetermined` + `Confidence: strong`
- `Concealment mode: juhud` + `Output shape: content`
- `P7 Stop-1 active` + `Output shape: content`
- `DO-orient: identity-perf | autotelic` + `Output shape: content`
- `Routing gate: V2-required` + `Matched modules: [any content module]`
- `Routing gate: semantic-discipline-required` + `Matched modules: [any doctrinal case file or attribute-content release]`
- `Routing gate: register-hold` + missing `What is withheld and why`
- `Routing gate: semantic-discipline-required` + missing `What is withheld and why`
- `Routing gate: stop-condition` + missing `What is withheld and why`
- `DO-orient: identity-perf` + `Matched modules: [any doctrinal case file]`
- `Reason-category: 3 or 4` + `Routing gate: open`
- `Concealment mode: anything other than clear` + `Output shape: content`. Register-hold governs Layer B whenever concealment remains live.
- `Claim-level: meta-epistemic | meta-ontological | meta-noetic` + `Matched modules: [first-order case file only]`. Higher-order burdens must clear before first-order dispatch.
- `Upstream findings` contains `semantic-neutralization-recontenting`, `semantic-neutralization-evacuation`, or `lexical-ontological-trap` + `Routing gate: open`
- `Matched modules` includes anticipated downstream modules or reserve owners not governing the current pass
- `P7 Stop-2 active` + `Next move` advertises another argumentative sequence rather than a boundary reset / one bounded question
- `Alignment state: alignment-advanced` + `Recognition strength` anything other than `strong`
- `Continuation eligibility: eligible-on-refresh` + missing `What remains live`
- `NS code: NS-6` + ontological burden live + generic restoration target. NS-6 ontological cases require a school-specific restoration target (`ḥudūth/khalq` distinction for the Muʿtazilī form; `kalām nafsī` doctrine for the Ashʿarī form), not a generic `bilā kayf` or generic foundationalist target.
- `NS code: NS-6` + ontological burden live + `Backbone predicates active` omits `O-1` and `C-1`. When NS-6 and the case involves divine attributes or speech, those predicates are minimum checks.
- `Structural pattern print` present + `Pattern-profile` absent or unset. Pattern print is subordinate to PF discipline; use `Pattern-profile: none` only when no PF overlay governs.
- `Structural pattern print` present + no routing, hold, release, or framing consequence. Pattern print without consequence is pattern theater.
- `Load-bearing node` present + downstream content released before the node is addressed. This violates upstream-node priority.
- `Framing notes` used to introduce new coverage content, prooftexts, or citations rather than to constrain release. Framing notes are not a citation bank.
- Tradition label used as the route while the structural node remains untyped. "Jewish", "Hindu", "Sufi", or "Buddhist" is not itself a routing owner.
- One upstream node cleared + all downstream material dumped at once. Refresh state and release only the next bounded move.
- `Next move` or visible output uses "Move 1 / Move 2 / Move 3" as essay sequencing
  without a prose state-change transition. Numbered headings are not RECURSE.
- `Matched modules` or visible prose names an M/E/F/R/V/P label, but `source_basis`
  and the bounded output do not show what operation the TTP actually performed.
- A visible `Operation:` line begins with generic prose (`address`, `discuss`, `explore`,
  `engage`, `consider`) instead of the closed operative verbs owned by
  `recursive-state-transitions.md`.
- A non-operative source-status is named in Layer B, but the operative-warrant sentence
  lacks the specific non-premise clause naming which contrast/opponent/history/genealogy/
  held/comparison element is not used as a premise.
- A held route or compact `held` noun phrase appears in Layer B as an answered topical
  commitment before a preceding state/noetic re-read explicitly releases it with
  `Released: <item>` or an equivalent release marker.
- Default-mode output ends with a bibliography, source list, or source-basis ledger
  without an explicit source/citation/audit request.
- Missing `Post-render gate` after a bounded restorative move. STOP, HOLD, RECURSE, and PARTIAL decisions are invalid until the gate has run.
- `Post-render gate: recursion_decision: STOP` while `remaining_live_distortions` names a live distortion, `newly_released_routes` is non-empty, or `next_eligible_pass` is anything other than `none`.
- `Post-render gate: recursion_decision: HOLD` while the remaining material has a present release signal and no stop, register-hold, semantic gate, thin-basis rule, or other hard rail blocks it.
- `Post-render gate: recursion_decision: RECURSE` while `next_eligible_pass` is `none`, or while the response fails to release the next eligible bounded pass.
- `Post-render gate: recursion_decision: PARTIAL` without naming the remaining live distortion and the next eligible pass that limits prevented.
- `Confidence` is anything other than `strong` *or* `Read status` is anything other than `dominant`, while `Decisive missing differentiator` is absent. This is the cosmetic-IR-formation guard: an IR that cannot name what would refine the read is paraphrase, not diagnosis.
- `Claim-level` is `meta-epistemic`, `meta-ontological`, `meta-noetic`, or `cross-level`, while `Current bounded operator` (or `Intervention target` / `Next move`) names a first-order doctrinal target rather than a higher-order function such as criterion test, tribunal test, authority-order correction, semantic / predication discipline, source-status / identity stabilization, foundational warrant, validation order, or category-set discipline. Higher-order vocabulary in the IR must be matched by a higher-order operator in the bounded move; otherwise the higher-order claim_level is decorative.

An IR with any of the above combinations has drifted.

---

## Compressed Form

For cases where a subset of fields is sufficient, the compressed form may be used:

```text
[IR - compressed]
Case: [family] | Claim: [type @ level?] | Pattern: [PF-x | none] | NS: [code] | Def: [code] | Conc: [mode] | Orient: [DO] | Gate: [routing gate] | Align: [state] | Rec: [strength] | Continue: [status] | Module: [matched] | Target: [restoration] | Next: [one move] | Post: [STOP|HOLD|RECURSE|PARTIAL; next=...]
```

The compressed form is not acceptable when architectural-layer fields are active. If the
level is omitted in compressed form, it means first-order after higher-order triggers
have been checked, not an unexamined blank.

---

## How the IR Prevents Cosmetic Compliance

Specific failure modes:

- **Cosmetic V1 compliance:** the response says V1 was run but the routing gate remains open while orientation or upstream blockers still prevent content.
- **Cosmetic framework-clearing:** the response names V2 but still loads content into the unreconstituted filter.
- **Cosmetic register acknowledgment:** the response acknowledges grief or register-hold but still outputs propositional content.
- **Current-pass blur:** the response advertises a queue of downstream modules rather than the coordination actually governing this pass.
- **Output-layer collapse:** the response notes `irad` or another register-hold and therefore omits the structural diagnosis from the complete output, leaving technique without the diagnostic architecture that justified it.
- **Held-route preview:** a stop or register-hold is named, but Layer B still previews the held doctrinal substance or future module chain.
- **Architectural drift:** the response satisfies workflow checks but states the restoration target argumentatively rather than restoratively.
- **Semantic-bypass compliance:** semantic neutralization or a lexical-ontological trap is active, but doctrinal content is released anyway. The IR catches this by requiring `semantic-discipline-required`.
- **Pattern-print theater:** the response names a structural pattern but does not identify the load-bearing node, intervention target, held downstream material, or existing route.
- **Argument-bank substitution:** the response treats a background topic as permission to list arguments, prooftexts, or citations before the live authority rule, criterion, or semantic blocker has been typed.

---

## Structural Validation Notes

These notes validate structural framing only. They do not create new coverage claims,
new case-family owners, or permission to release comparative-religion content. Each
fixture names an internal pattern print and the existing routes that govern the next
move.

### 1. DO-15 moral objections

```text
Structural pattern print: validation inversion / Level A vs Level B collapse / imported moral tribunal
Load-bearing node: moral criterion and validation order
Collapse radius: detailed fiqh, hudud detail, gender jurisprudence detail, slavery-history monograph
Intervention target: expose the criterion, preserve real fitri moral recognition, test whether the specific ruling under full conditions violates the internal criterion
Framing notes: do not deny moral perception; do not capitulate to the imported tribunal; do not answer with "rarely applied" as the whole response; do not defend historical abuse as shari'ah
Existing route: FPD + philosophical-usurpation Type D + V2 + existing DO-15
Held: detailed fiqh and legal-history expansion
Must not dump: citation bank, fiqh monograph, apologetic minimization, abuse-as-doctrine defense
```

### 2. Sufi kashf / tariqah authority

```text
Structural pattern print: authority inversion / kashf-as-tribunal / charismatic authority as epistemic override
Load-bearing node: authority jurisdiction of kashf, shaykh, or tariqah relative to revelation
Collapse radius: broad Sufism taxonomy, contested-practice fiqh, anti-Sufism polemic
Intervention target: classify whether the experience or authority claim has jurisdiction over revelation
Framing notes: do not debate whether the event occurred before jurisdiction is classified; separate authority wound from authority tribunal
Existing route: FPD + philosophical-usurpation + NS-8/P7 as needed + M7/M9 if vocabulary governs
Held: Sufism owner content, practice adjudication, global attack/defense of Sufism
Must not dump: anti-Sufism polemic, tariqah history, contested practice rulings
```

### 3. Jewish Torah-completeness / final-prophethood

```text
Structural pattern print: closed-canon veto / selective scriptural arbitrage / prior-recognition dispute
Load-bearing node: whether Torah, canon, or rabbinic closure functions as veto over later divine speech
Collapse radius: biblical prooftext use, comparative-prophethood content, Jewish owner content
Intervention target: classify impossibility, authority, evidence, canon, interpretation, or identity/covenant wound before prooftexts
Framing notes: do not make external prooftexts the foundation; do not treat Jewish and Christian objections as identical
Existing route: FPD + DO-14/V10/RT + comparative-prophethood/DO-10 as appropriate
Held: biblical prooftext dump, broad Judaism coverage, new Jewish owner content
Must not dump: lists of prooftexts or citations before source-use discipline
```

### 4. Arya Samaj Qurʾān critique

```text
Structural pattern print: external criterion as tribunal / Vedic-reformist reason claim / Satyarth-Prakash-style polemical standard
Load-bearing node: criterion used to judge Qurʾān, prophecy, divine attributes, resurrection, or law
Collapse radius: verse-by-verse Qurʾān defense, Hindu owner content, exact Sanaullah citations
Intervention target: disclose whether "reason/common sense" is sound reason or a school-bound polemical criterion
Framing notes: do not treat Arya Samaj as Advaita; do not quote noisy Urdu OCR as exact source
Existing route: FPD + V2 + reason-disambiguation + M9 if divine predication is live + RT if source authority becomes central
Held: Hindu Arya owner, Sanaullah exact quotations, broad Hinduism coverage
Must not dump: verse defenses, OCR citations, "Hinduism covered" language
```

### 5. Advaita

```text
Structural pattern print: non-duality / illusion ontology / Creator-creation collapse / higher-lower truth tribunal
Load-bearing node: whether nondual ontology is functioning as the upstream category-set over Islamic tawhid
Collapse radius: ordinary polytheism response, Advaita owner content, Hinduism coverage claim
Intervention target: distinguish Islamic tawhid, monism/nonduality, and mystical or poetic language before content release
Framing notes: do not collapse Advaita into popular idol worship; do not claim authorized Advaita coverage
Existing route: M9 + metaphysical-architecture + philosophical-usurpation if nondual ontology is installed as tribunal
Held: Advaita owner content and broad Hinduism coverage
Must not dump: generic idol-worship answer when nondual ontology is live
```

### 6. Buddhist anatta / impermanence

```text
Structural pattern print: self-negation / identity-continuity pressure / two-level discourse / impermanence category pressure
Load-bearing node: whether the claim denies enduring subjecthood, denies independent ego, or uses therapeutic anti-essentialism differently from metaphysical denial
Collapse radius: Buddhist owner content, primary Buddhist-source claims, broad Buddhism coverage
Intervention target: clarify self, nafs, ruh, person, continuity, moral responsibility, and created dependence before response
Framing notes: do not treat anatta as simple mate
