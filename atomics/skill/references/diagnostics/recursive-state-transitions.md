---
id: recursive-state-transitions
module_class: governance
canonical_path: skill/references/diagnostics/recursive-state-transitions.md
contract_version: "0.4.0.0"
load_when:
  - after a bounded restorative move has landed
  - deciding STOP / HOLD / RECURSE / PARTIAL
  - auditing state re-read, held-route reassessment, or same-response recursion
routing_effects:
  - defines abstract STOP / HOLD / RECURSE / PARTIAL semantics
  - requires post-render re-entry before closure
  - blocks premature STOP while an eligible live burden remains
  - blocks recursive argument dumps and inherited module stacking
emits:
  - recursive_state_transition
  - post_render_gate
  - state_carry_partition
blocks:
  - premature STOP
  - held-as-never-answer
  - state-re-read-as-user-reply-only
  - recursive dump after one refresh
companions:
  - framework-pipeline
  - diagnostic-ir
  - routing-precedence
  - output-release
  - diagnostic-render-contract
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

# Recursive State Transitions

PACK-SPEC note: this file functions as a recursive-state contract owner. For future normative
edits, use `docs/spec-authoring-pack.md`; keep uppercase MUST / SHOULD / MAY intentional and
backed by examples or checks.

This file is the canonical abstract owner for STOP / HOLD / RECURSE / PARTIAL
state-transition semantics. It governs post-render re-entry, no-premature-STOP discipline,
same-response recursion eligibility, PARTIAL vs STOP, and the state carry/reset/re-evaluation
partition after a bounded move.

## Authority Boundary

This file owns only abstract recursive state-transition semantics.

- `references/procedures/P7-restoration-stops.md` owns concrete stop instances.
- `references/diagnostics/diagnostic-ir.md` owns typed fields, schema carrier, and the
  `post_render_gate` record.
- `references/rubrics/output-release.md` owns release amount, release order, and hold/release
  discipline before render.
- `references/rubrics/diagnostic-render-contract.md` owns visible render mode.
- `references/diagnostics/routing-precedence.md` owns route order and suppression.
- `references/diagnostics/framework-pipeline.md` owns the pipeline audit surface and forbidden
  shortcut chart.

This file does not create routes, module activation rules, IR fields, source owners, or coverage
claims.

## Runtime Notation / Meta-Noetic Memetic Compression Layer

This notation is operative compression for existing runtime behavior, not decorative formalism.
It creates no IR fields, route IDs, PF codes, module owners, or schema keys.

Legend:
- `N` = noetic structure / operative noetic frame.
- `m` = memetic claim / criterion / authority-node.
- `τ` = tribunal / evaluative criterion.
- `σ` = source-status.
- `B` = live noetic burden.
- `s` = operative submove.
- `H` = held set.
- `R` = state/noetic re-read.
- `Δ` = state change.
- `∇` = route-gradient read over live field pressure.
- `∇·` = divergence-like residual outward pressure diagnostic.
- `∇×` = curl-like circularity / loop diagnostic.

Core runtime:

```text
Input -> IR(N,m,τ,σ) -> ∇ route-gradient -> B -> {s1...sn} -> Land(B) -> Δ -> ∇·/∇× diagnostics -> LoopBreak if licensed -> R(H,Δ) -> 𝒞(Ψᴺ) -> STOP/HOLD/PARTIAL/RECURSE
```

LoopBreak is conditional, not decorative. If `∇×T` is checked and non-null, the output must
either license `LoopBreak:` with target, owner-ground, `Δ` effect, post-break reread, and resulting
hold/closure state, or carry the loop into HOLD/PARTIAL/RECURSE. If `∇×T` is checked and null,
render compactly as `LoopBreak: not needed` / `not licensed` / equivalent when the loopbreak
surface is in scope. If cyclic pressure was not checked, do not silently imply a loopbreak; use
ordinary prose unless the field-diagnostic surface requires a compact not-licensed status.

Burden/submove notation:

```text
ⁿBᵢ = i-th operative submove inside the n-th burden-cycle
nBi = plain-text equivalent
B1.s1 = accepted legacy/checker alias for ¹B₁ where needed
```

Examples:

```text
¹B₁ = 1B1 = burden 1, submove 1
¹B₂ = 1B2 = burden 1, submove 2
²B₁ = 2B1 = burden 2, submove 1
```

Submove / recursion:

```text
sᵢ != Bᵢ
¹B₁ -> ¹B₂ -> ... -> Land(¹B) -> R(H,Δ)
Land(¹B) -> R(H,Δ) -> ²B₁
```

Gloss: `ⁿBᵢ` names the i-th operative submove inside the n-th burden-cycle. A burden may
contain multiple operative submoves before it lands; a submove is not automatically a new
burden-cycle. A new burden begins only when `Land(B)` and `R(H,Δ)` license it.
`Land(B)` is a state transition, not a formatting reward. For both initial `𝔅_LA` burdens and
generated `𝔅_MRP` burdens, the submoves must have enough owner/TTP mass to change the live field:
they identify the exact claim, pressure, route, predicate, source-status, consequence, or
affective/noetic move being worked; apply the owner operation; record the state delta; and show why
that delta discharges the burden. A burden with only labeled Target/Operation/Result/
Contribution fields remains unlanded when those fields are conclusion-shaped. Bounded, local, or
short surface form is not a low-mass license; low-mass concise treatment requires diagnostic proof
that hidden premise, dependency, source/worldview, predication/category, proof-stack, recoil, and
closure-risk pressures are absent.

Collapse:

```text
Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB
-> {facet1...facetn} ⊂ {s1...sn}
-> ¬RECURSE
```

Gloss: same tribunal, source-frame, and claim-cluster collapse into one burden-cycle unless
`R` licenses a genuinely new input-anchored `B`.

Derived register bridge:

```text
Sameτ ∧ Sameξ ∧ SameΩ ∧ Sameσ ∧ Sameκ
-> facets ⊂ {s1...sn}
-> ¬RECURSE

ⁿBᵢ[OP] : target -> operation -> result -> ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ
Land(ⁿB) -> R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ) -> STOP/HOLD/PARTIAL/RECURSE or ⁿ⁺¹B
```

Gloss: this is a formal/specification bridge for current behavior. `ξ`, `Ω`, `♥`, `μ`, and
`κ` are derived lenses over existing warrant, ontology, register, meta-noetic memetic, source,
collapse-radius, and reread governance. They do not create mandatory IR fields. `ΔⁿB` is the
local landed state change inside the current burden; `ⁿ⁺¹B` is a new burden-cycle only when
`Land(B) -> R(H,Delta)` licenses it. `κ` is the downstream dependency set consumed by reread,
not a generic TODO list.

General noetic-selection / register-control reread gate:

```text
Land(ⁿB) -> R(H,ΔⁿB{heart,xi,Omega,sigma,mu},Δkappa)
```

This gate is mandatory whenever a live burden lands. It does not assume the selected N frame
is known at design time: the runtime must scan the noetic-structure selection space, select or
hold candidate/held N frames, activate live registers, and let `R` decide STOP, HOLD, PARTIAL,
RECURSE, or NewB from the refreshed state. The selected execution path is the release order
over the live field, not the whole field itself. If several noetic-structure selections are
valid, `R` rereads the whole burden/dependency/register/route field after each `ΔⁿB` / `Δκ`,
so alternate valid structures, hidden dependencies, circularities, unresolved pressures, and
residual candidate routes are addressed, integrated, discharged as duplicate/derivative,
explicitly held with reason, or carried forward into RECURSE. The formalism is valid only when
it changes control: owner eligibility, held material, hold/release posture, burden selection,
collapse radius, reread, or closure state.
Compact output should recover the equivalent of held set, live remainder, newly released or newly
blocked routes, and next eligible pass / STOP-HOLD-PARTIAL-RECURSE-COMPLETE status. `𝒞(Ψᴺ)` is
agent/runtime execution-field closure only: it must identify COMPLETE, STOP, HOLD, PARTIAL, or
RECURSE relative to the runtime field, and it never means interlocutor acceptance, persuasion,
conversion, guidance, or soul access. `Ψᴵ` remains a diagnosed interlocutor field under
uncertainty; alternate reads stay held when discourse evidence underdetermines the profile.
When a Closure/Reconstruction Witness is rendered, `R(H,Δ)` must also account for the initial
burden set through terminal states or explicit carry/hold decisions. The dependency graph records
which burdens depend on prior landing; the coverage proof records whether every initial burden has
one terminal state; the collapse proof is stronger and requires neutral `∇·B` plus null/resolved
`∇×κ` for the scoped field.
The initial burden set is a pre-release Layer A / Diagnostic IR enumeration. It must be declared
before the terminal-state accounting that closes the witness. New burdens discovered by `R(H,Δ)`
are newly live or next-pass candidates, not retroactive additions to the original initial set.
If `xi` (warrant / authority / proof-status), `Omega` (ontology / predication / dependence),
`sigma` (discourse / pattern state), `mu` (carrier or reproduction vector), `kappa`
(downstream dependency set), or `H` (held burdens) remain live after `Land(B)`, `R` must force
another burden, HOLD, PARTIAL, or explicit clearance. It may not STOP or mark COMPLETE while
downstream dependencies remain. Concrete dependencies are case-shaped: source-authentication
may expose transmission/testimony routes; moral protest may expose predicate/tribunal routes;
named worldview may expose source/worldview-frame routes; doubt cases may expose register/P7
routes. These are control checks, not topical argument-bank entries.
When a compact MRP block is rendered for that transition, it is a parseable transition record:
literal `[Mid-Reread Pressure]`, `Target: Bn` / `Target: ⁿB`, route-bearing `R(H,Δ): held routes
rechecked: ...; live remainder: ...; release/next: ...`, then the fixed field lines. `Route:` is
only `STOP`, `HOLD`, `RECURSE`, or `LoopBreak(∇×T)`; destinations and explanations belong in
`R(H,Δ)`, `MRP resultant`, and `Graph delta`. If STOP follows any named held route, each named
route must be worked, generated, HOLD/PARTIAL-routed, or explicitly classified as
non-load-bearing with reason before COMPLETE may be claimed.

Plain `∇` is the route-gradient read over the live field before burden release. Formally, it is a
route-ranking/preorder pressure read over eligible routes, not a literal vector gradient. It identifies the
direction in the noetic/burden/dependency/register/route pressure landscape where the next
released burden is expected to produce the greatest diagnostic reduction, closure progress, or
dependency clarification. In default render it appears in Layer A's gate/release decision, not as
a retrospective decoration after Layer B: `∇ route: Bn pressure highest — [reason] over [held
alternatives]`. Routing remains owner-gated and catalogue-constrained: V1, Diagnostic IR, routing
precedence, profile signals, and catalogue eligibility are the inputs and boundaries for the
gradient read. Plain `∇` ranks or explains release pressure among eligible routes; it is not a
truth/warrant metric, not free-form intuition, not a bypass around gates, not a replacement for
`Δ`, `∇·`, or `∇×`, and not a deterministic route freeze when multiple valid candidate structures
remain live.

Noetic structures, burdens, submoves, dependencies, registers, routes, and closure pressures are
not scalar objects. They are relational field states in token/noetic space: directed dependency,
residual outward pressure, circularity, overlap, conflict, and unresolved route pressure can all
remain after a local burden lands. `Δ` operators compute event-local transition over the current
burden/field state; `∇·` and `∇×` read the `Δ`-produced field state. `del-dot` and
`del-cross` are ASCII aliases for `∇·` and `∇×`, not separate operators. `∇·` reads
divergence-like residual outward pressure in a target-explicit field. `∇×` reads curl-like
circularity, rotational dependency, or unresolved cyclic pressure in an explicit target field.
An acyclic downstream burden chain is residual divergence, not curl: `Bn -> Bn+1` remaining
live after `Land(Bn)` means `∇·T` is non-neutral while `∇×T` is null unless a real loop, churn,
hidden-framework recoil, label-pressure, or dependency rotation is also present.
The target may be `κ` (`∇·κ`, `∇×κ`) or another owner-defined noetic, burden,
dependency, register, or route target (`∇·B`, `∇×B`, `∇·♥`, `∇×ξ`) when the target
and control effect are clear. These diagnostics do not apply to scalarized one-point summaries,
are not transition operators, do not replace `ΔⁿB` or `Δκ`, and do not prove execution by
symbol. Closure is licensed only when residual divergence/curl pressure is cleared, integrated,
discharged, held with reason, or carried into RECURSE/PARTIAL.

If `∇×T` remains nonzero after a burden lands, the runtime must decide whether to HOLD/RECURSE
or license a loop-breaking submove. Canonical loop-breaking form: `LoopBreak(∇×T)`. The target
`T` must be explicit, and the submove must name the target loop, the owner-licensed grounding
source, the burden/submove used, the `Δ` effect, the post-break `∇×T` reread, and the resulting
closure/HOLD/PARTIAL/RECURSE state. Valid grounding sources are owner-bound: fiṭrah, `ʿaql
ṣarīḥ`, necessary knowledge, definition discipline, direct contradiction exposure,
source-status correction, or another owner-licensed non-circular ground. `LoopBreak(∇×T)` is not
arbitrary assertion and is a partial licensed transition, not a total transition. If no loop-breaker is licensed, nonzero curl must be held with reason or
carried into RECURSE/PARTIAL.

A COMPLETE closure in any multi-burden or register-active case must visibly account for
selected and held `N` frames, live registers, active or cleared owner/TTP child modes,
`Delta-nB`, `Delta-kappa`, target-explicit `∇·` / `∇×` results, burden dependency graph, and
remaining `kappa` / `H` status. The dependency graph uses compact edge notation such as
`B1 -> B2, B3, B4, B5` for root-to-serial dependencies or `B1 ∥ B2 -> B3` when a later burden
depends on multiple landed burdens. If the closure cannot account for these dependencies without
turning into a topic dump, it must mark PARTIAL or RECURSE instead of COMPLETE.

Terminal formalism: `𝒞(Ψᴺ)` names the positive closure-field condition over the agent execution
field, not mere checklist exhaustion. STOP is licensed only when the live field reaches the
target configuration: input-anchored burdens are landed, integrated, discharged, held with reason,
or marked PARTIAL/RECURSE; residual `∇·` pressure is neutral, bounded, or explicitly carried;
residual `∇×` loops are broken, resolved, or explicitly held; and the released response can
reconstruct the route from diagnosis to restoration without hidden live pressure. `N_fiṭrī ∧
ʿaql ṣarīḥ` names the restorative terminal orientation in that agent execution field: fitri
recognition plus sound reason after the governing misread loses control. It is not a shortcut
around burden landing, not proof-by-symbol, not a long default formalism exposition, and not a claim that the interlocutor has internally accepted truth.
A compact `𝒞(Ψᴺ)` marker is required when COMPLETE/STOP is rendered, because closure is licensed
by positive field configuration rather than checklist exhaustion.

Field boundary: `Ψᴺ` names the agent/runtime noetic execution field. `Ψᴵ` names the diagnosed
interlocutor noetic field inferred from discourse, profile, register, response, and source-status
evidence. A released burden in `Ψᴺ` does not directly rewrite `Ψᴵ`; it produces a
language-mediated partial coupling relation, `T_lang: Ψᴺ ⇢ Ψᴵ`. It is not an isomorphism, not a
surjection, and not a guaranteed update operator on `Ψᴵ`. Final restorative boundary text must name
this coupling when closure or final counsel is rendered. Coupling is assessed by whether the
released response preserves identity, avoids deformation, addresses live burdens, and provides
conditions for `Ψᴵ` to reconfigure toward fiṭrah and `ʿaql ṣarīḥ`. This is a runtime/output
boundary: it does not assert access to the interlocutor's soul, guarantee acceptance, replace
source-status discipline, treat profiles as total identity, or claim the agent controls guidance.

Cross-family child-mode landing:

```text
OP_family -> target -> operation -> result -> Land(B)
-> R(H,Delta{heart,xi,Omega,sigma,mu},Delta-kappa)
-> STOP/HOLD/PARTIAL/RECURSE or NewB
```

Gloss: M9, PM, AS, DW, DA/DS/HK, OQ, and MM child modes all land through the same state
transition discipline. A child operator may clear one register while exposing another, but the
next owner is licensed only by reread. If the noetic frame remains unknown-pattern-typed, `R`
keeps `N` held while allowing the typed owner result to change `H`, `kappa`, source-status,
release posture, or NewB eligibility. A named school, family, affiliation, or profile label
does not become finite `N` merely because an operator landed.

Source-status:

```text
σ ∈ {contrast, opponent-position, genealogy, historical note, held material, bounded comparison}
-> σ_context != σ_warrant
-> σ != operative warrant
```

Gloss: non-operative sources cannot become proof without explicit reclassification.

Noetic-frame non-equivalence:

```text
N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī
N_Ashʿarī != N_Māturīdī != N_Taymiyyan
N_AT != N_Ashʿarī[*]
N_AT != N_Māturīdī[*]
N_Ashʿarī[*], N_Māturīdī[*] = family labels, not automatic operative N
N_Ashʿarī[x] != N_Ashʿarī[y] when the live predicate/warrant/criterion/authority-order differs
N_Māturīdī[x] != N_Māturīdī[y] when the live predicate/warrant/criterion/authority-order differs
family label != operative N
shared vocabulary != shared warrant
shared conclusion != shared warrant
verbal agreement != operative support
```

Gloss: `N_AT` canonicalizes repo routing aliases for the Atharī/Taymiyyan/Salafī/Wahhābī
operative frame; aliases are not counted as multiple warrants. This is not a historical,
sociological, polemical, individual, movement, or institutional identity claim. Contradictory
or family-level noetic frames are not co-valid operative supports; only the selected operative
`N` may warrant the move.

Held carry:

```text
H(n+1) = (Hn ∪ InputLive_n) - Released_n
```

Gloss: held material carries across cycles until released or resolved.

Re-read:

```text
Land(B) -> R
R required before STOP/RECURSE
```

Gloss: a burden must land before re-read; the visible reread surface is the MRP activation
record whenever the reread licenses closure, HOLD, PARTIAL, LoopBreak, or recursion.
`R(H,Delta)` is a state-transition judgment, not a formatting marker. After each `Land(B)`,
refresh the current noetic state and decide whether to continue to the next already-present
burden, hold/defer it, skip it because it no longer applies, mark PARTIAL/limit, trigger a
bounded reroute need because the live state materially changed, or close because no
input-anchored burden remains.

Mid-reread pressure: when `R(H,Δ)` is deciding whether an apparent post-landing burden is stable,
genuinely downstream, partial, recoil-bound, churn, or reminder/reorientation pressure, load
`references/tactics/TTP-MRP-mid-reread-pressure.md`. MRP freezes the landed `ΔⁿB`, tugs the
dependency graph through closure-witness machinery, activates the relevant existing pressure
owners for hidden-framework recoil / label-pressure / entailment pressure / doubt-churn /
reorientation, then records which route their outputs license: STOP, HOLD, RECURSE,
LoopBreak(∇×T), or closure witness.
If MRP finds a genuine new dependency, `R(H,Δ)` attaches the graph edge and chooses RECURSE. If the
pressure is partial but real, choose HOLD. If it is churn, label-pressure, or unlicensed recoil,
use LoopBreak or STOP without proof-stacking. If the reread is stable, render the closure witness.
MRP is not a truth/warrant metric and does not make `T_lang: Ψᴺ ⇢ Ψᴵ` guarantee uptake.

B-complexity:

```text
ComplexB -> {s1...sn} -> Land(B) -> [Mid-Reread Pressure] -> R
AtomicB -> s1 -> Land(B) -> [Mid-Reread Pressure] -> R
```

Gloss: distinct hidden premises, criteria, predicates, source-status forks, release gates, or
restoration vectors inside the same live burden make `B` complex. `AtomicB` is valid only when
one owner-specific operation can change the burden-state without leaving internal premises,
predicates, or gates unoperated.

## State Model

`STOP` is valid only after state re-read confirms that the current governing blocker has been
addressed, no eligible live burden already present in the original input remains live, no held route
became releasable after the move, and P7 permits stopping.

`HOLD` is valid only when remaining material exists but its release signal is absent because a
stop, register-hold, semantic gate, thin-basis rule, or other hard rail still blocks it.

`RECURSE` is required when another live distortion remains in the same input, or when a held route
becomes newly eligible after the current pass clears its blocker.

`PARTIAL` is required when token, tool, or interaction limits prevent completion while recursive
pressure remains. Do not emit a false STOP in that condition.

Planned continuation is never unconditional. In Level 1/2, the model performs this refreshed
diagnostic judgment directly under SKILL/governance. In Level 3, `continuation_queue` is a
planned route; each queued burden still remains conditional on the preceding `Land(B) -> R`
confirming that the next burden is still input-anchored, live, and unblocked.

Structural attachment fidelity is part of this transition rule. The runtime must preserve the
local sequence and attachment of each burden step:

```text
ⁿBᵢ / nBi -> owner-floor Target/Operation/Result -> Land(ⁿB) -> R(H,Delta) -> next state decision
```

Marker presence is not execution. A trace or response that groups all reasoning first, all
owner/checker markers afterward, or all state decisions at the end has flattened the control
state even if the same labels appear somewhere. Each marker must govern the burden step next to
it; `Land(ⁿB)` must summarize the cumulative state delta from its submoves. Otherwise the
output is a component-tour / structural-flattening failure.

In hard/default output, Restorative Response and Closing Formulation are licensed only after
the final state re-read for the answer. If `R(H,Delta)` names a remaining input-anchored
burden and no hold, register, semantic, thin-basis, source-use, or limit gate blocks it,
the next action is the next bounded burden-cycle, not rhetorical closure. If the next
bounded pass cannot fit, mark PARTIAL with the next live burden.
MRP named pressure counts as state re-read pressure here: proportionality, hiddenness/coercive
guidance, source-worldview, moral-grounding, owner-floor, owner-body, non-neutral `∇·T`,
non-null/held `∇×T`, or graph-edge pressure must be released and landed, held with reason, or
marked PARTIAL before STOP/COMPLETE or final response sections are licensed.

Input-anchored burden means more than an explicit question-marked subrequest. It includes
supporting premises, contrasts, public/private partitions, source-status rules, translation
demands, and moral or epistemic criteria already present in the user's surface discourse.
After the blocker that held them clears, they must be rechecked as possible next burdens
rather than dismissed as future topics.

If a state re-read enumerates remaining input-anchored burdens, "only if requested" is not
a valid STOP reason unless a named hold gate blocks release. The claim that remaining material
requires its own bounded pass licenses RECURSE or PARTIAL; it does not license rhetorical
closure.

## TTP Entry / Exit Criteria

Recursion is auditable only when each TTP has entry criteria, operation criteria, and exit
criteria. These criteria are internal runtime checks; they do not create new routes, IR fields,
or visible default-mode template slots.

**TTP entry criteria:**

1. Validated IR exists and names the current live burden.
2. Routing precedence selected one current bounded operator, not a route chain.
3. The TTP owner is justified by the current IR state or by refreshed state after a prior burden-cycle.
4. For hard/multi-burden `ⁿBᵢ`, the active owner body or compiled bundle
   section is loaded/read, unless that exact section is already present in active context.
   Package availability, map presence, or bundle co-location is not access. If access is
   absent, the route is `PARTIAL / OWNER-BODY-NOT-LOADED` with the missing owner/path,
   not generic prose.
   In an MRP activation record this appears as `Route: HOLD` plus
   `Boundary: PARTIAL / OWNER-BODY-NOT-LOADED: <missing owner/path>`; after that boundary,
   closure witness, Restorative Response, Closing Formulation, and "refuted"/"closed" language
   for the blocked burden are not licensed.
5. The TTP has a bounded target inside the active live noetic burden.
6. Output-release permits the operation now; otherwise the route is HOLD or PARTIAL.
7. No P7 stop, register-hold, semantic gate, thin-basis rule, or absent release signal blocks it.

**TTP operation criteria:**

1. The operation must do the owning TTP's work, not merely name the TTP label.
2. Operative submoves must preserve owner identity plus target -> operation -> result.
   Where the owner has a compact ID, attach it locally to the submove label/body (for example,
   `¹B₁ [FPD]`, `¹B₂ [M1]`, `¹B₃ [M9]`; ASCII fallback only if needed) rather than hiding
   it in a later trace line.
   Generic "Operative submove N" labels are insufficient for module-backed owners unless the
   owner ID is also local to that submove. A later trace list cannot retroactively attach an
   owner to generic prose.
3. `Operation:` lines must begin with one of the closed operative verbs already used by
   the framework: `split`, `distinguish`, `test against own grounds`, `disambiguate`,
   `classify`, `audit`, `reclassify`, `narrow`, `expose`, `re-read`, `sequence`,
   `refuse jurisdiction of`, or `clear`. Generic verbs such as `address`, `discuss`,
   `explore`, `engage`, or `consider` are non-operative operation verbs and do not
   satisfy execution.
4. Multiple operative submoves may land one live noetic burden, but they remain internal until the burden landing.
5. A downstream TTP cannot inherit eligibility from the initial route read; it must be selected
   from the refreshed state after the prior bounded operation.

**Owner-specific operation floor:**

Generic `target -> operation -> result` syntax is not enough. The operation must apply the
owning file's minimum operation floor: the specific pressure dimensions, branch tests,
definition splits, or criterion tests required by that owner. A TTP named without its
owner-specific operation floor is label surface-compliance failure even when a Target/Operation/Result line
is present.

In Level 3, `pressure_dimensions` may appear as structured route/check data. In Level 2
or other scriptless execution, the same idea remains an internal render-governance floor,
not a public field to print. The output must visibly execute the relevant pressure:
imported criterion authority for FPD, self-ground testing for M1, hujjah/accountability
and coercive-guidance narrowing for do-second-loop, sound-reason/proof-status repair for
V2, source/noetic-frame consequence for M8, restoration bounded to landed burdens for P1,
testimony/tawatur/authentication pressure for transmission owners, predicate/category
pressure for predication owners, and register-hold/pastoral sequencing for grief owners.
Hard/manual graphable output must make the owner mechanism visible enough to reconstruct:
source-status/authority-order sorts citations, source-prestige, hidden support, and source
function; do-christian-extensions identifies the Christian pressure family and model/fan-out route
before content release, and for DO-12 Trinitarian model pressure its ACT / field_witness operation
is `model-identification`, never bare `route`; doubt-vs-skepticism distinguishes normal doubt from skeptical methodology,
the evidence-demand or modal-veto tribunal, and the burden inversion/LoopBreak consequence; P7
names STOP/HOLD/PARTIAL, held-route boundary, and reopen condition. Unknown but source-owned
catalogue owners remain eligible, but their operation body still needs a local mechanism, action,
state change, and contribution to Land.
If those pressures do not change claim-state before `Land(B)`, the burden has not landed.
If a source-request burden has several source functions, each function must remain attached
to the submove it governs. A global source list or one generic revealed text does not preserve
state when the route needs separate hujjah, guidance/non-compulsion, fitrah/ayat,
mercy/justice, repentance/return, testimony, or predicate-source operations.
Final restoration is licensed only after those source functions have either landed or been
held. A closing synthesis cannot be the first place where mercy/justice, Creator-right,
repentance/return, worship-worthiness order, testimony, or predicate-source pressure is
operatively supplied. If such a function remains live at `R(H,Delta)`, it is a next
burden-local `s`, a licensed `NewB`, HOLD, or PARTIAL--not final closure.
Hard/compound recursion also requires a reconstruction-faithful Layer A before execution:
claim level, pattern/deformation, reason category, concealment, DO-orient, live burden,
source-status/noetic-frame, held/released state, and gate/release decision. Without that
compact noetic frame, `Layer B` is arguing before the state has been typed.
When source-worldview is the live frame, `s` must name the concrete criterion-bearing
commitment being traced from input anchors or bounded source knowledge. A generic
source-worldview label without the operative commitment does not preserve state attachment.
When the live pressure is testimony, predication, grief/register, kalamic proof-order, or
another family-specific burden, do not relabel it as source-worldview merely to satisfy M8;
the consequence trace must stay family-local.

Default output must not narrate that an owner floor was applied. Phrases such as "owner
floor is applied", "owner-floor pressure", "the TTP has to change something",
"burden-completeness check", or "the operation is bounded to the target named above" are
test-harness proof, not TTP execution. If the public answer needs target -> operation ->
result, the terms must be filled with case-specific pressure and visible state change,
not compliance explanation.
Canonical scriptless output must also avoid route/check harness commands or verdicts such as
"execute queued owner", "execute first-live owner", "owner-floor passed", "validation passed",
`smoke_kind`, `validation_fidelity`, `execution_fidelity`, `route_plan`, `features.json`,
`check_execution`, or repo/dev harness proof claims. Owner identity is allowed only as a
human-facing local submove anchor tied to operation and state change, not as a queue command.
`Owner-floor:` lines and `B<N>.s<M>` markers remain repo/dev-harness or legacy/checker
shapes; canonical scriptless output should prefer `¹B₁ [owner ID] - plain operation`, using
ASCII `1B1` only when Unicode is unsupported, with the owner-specific operation shown in
ordinary case prose.

Each TTP owner used in a burden-cycle must be able to answer:

1. Which owner rule or anchor made this TTP eligible?
2. Which exact premise, predicate, criterion, or warrant is the target?
3. Which owner-specific operation was performed?
4. What result changed the current burden-state?
5. Which remaining material is held, released, or newly eligible after the result?

**TTP exit criteria:**

1. The pass states or internally records the TTP result.
2. The burden landing is known: landed, held, partial, or failed to clear.
3. state re-read rechecks held routes and remaining same-input live burdens.
4. The next decision is STOP, HOLD, RECURSE, or PARTIAL.
5. Restoration synthesis or pastoral note appears only after this exit and refresh license it.

**Land(B) requirements:**

`Land(B)` is not a phrase in the output. The burden has landed only when:

1. every materially necessary submove for the released live burden has either been operated
   on, explicitly held by a gate, or marked PARTIAL with a concrete limit;
2. at least one owner-specific result changes the live burden's status, not merely its
   wording;
3. the cumulative-state delta is known: what the burden looked like before the operation,
   what changed after the operation, and why the next state is narrower, cleared, held, or
   partial;
4. no held route has been silently answered inside Layer B;
5. state re-read can identify STOP, HOLD, PARTIAL, or a licensed NewB from the changed
   burden-state.

A sentence such as "this burden lands" after generic prose is invalid unless the preceding
operation supplies the cumulative-state delta.

If entry criteria are missing, the TTP is not activated. If operation criteria are missing, the
TTP is label surface-compliance failure. If exit criteria are missing, recursion is unauditable and closure is
premature.

## Depth And Stop Guards

Depth is governed by live-burden traversal, not by how many arguments or headings can be written.
This is not a shortness rule. In hard, compound, or deformed cases, each released depth
increment must receive enough owner-floor execution, theological substance, and restoration
work to land before state re-read. A single compact Layer A plus thin topical sections is a
false depth signal, not governed traversal.
Each recursive depth increment requires:

```text
prior burden landing -> state re-read -> next input-anchored live burden -> new bounded operator
```

Depth guard rules:

- No recursive depth increase without a burden landing and state re-read.
- No repeated operator at the next depth unless refreshed state supplies a new bounded target.
- No downstream release from the initial itinerary; refreshed state must license every next pass.
- No total downstream dump after one refresh.
- No submove blur or explosion: if a burden requires more than three major operative submoves,
  the runtime must run the submove saturation gate as a cohesion audit. The gate decides
  whether the next move remains a distinct `s`, becomes a NewB after `R`, is held, or is
  PARTIAL; it is not a count cap and not a merge license.
- If response, tool, or interaction limits prevent the next eligible burden, use PARTIAL with the
  concrete limit and the named next live burden.
- If the next live burden remains live but a release signal is absent, use HOLD with the blocker.
- STOP requires proof that no eligible same-input live burden remains, no held route became eligible,
  and P7 permits closure.

### Submove Saturation Gate

Before adding another major `s` inside the current `B`, ask whether the candidate submove
still shares all of the following with the active burden:

```text
same operative target-family
same tau / claim-level
same source/noetic frame
same claim cluster
same restoration vector
not already handled by a prior submove result
```

If the answer is yes, the submove may remain internal to `B` when it is materially necessary
for burden completeness. If the answer is no, do not keep expanding the submove list. Run
`Land(B) -> R` and let the re-read decide STOP, HOLD, PARTIAL, or NewB.

More than three major operative submoves inside one burden-cycle triggers the submove
saturation gate. If the gate records necessity and cohesion, the additional submove remains
inside the burden as its own distinct target -> operation -> result. Otherwise the additional
move is either a licensed NewB after re-read, held, or PARTIAL. Size, component availability,
or a desire for a fuller answer never licenses an additional major submove by itself.
The gate is never a consolidation license: active TTP/operator functions must remain distinct
submoves or later burden-cycles. If runtime limits prevent that distinct execution, mark PARTIAL
with the specific unlanded submove rather than merging it into a generic operation.

The convergence target is governed recursive sufficiency: the live same-input noetic structure has
been restored as far as the current gates permit. The target is not maximal topic coverage and not
shortest possible prose.

## Post-Render Re-Entry Gate

After every bounded restorative move, run state re-read before closure. The post-render gate asks:

1. What cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. What is the next eligible pass, or is it `none`?
6. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

The gate is not a new routing pass. It is the enforcement point that keeps the validated IR live
after the response has made a bounded move.

Layer A owns first-pass burden discovery. The initial read inventories the ordinary burden nodes
that are already present in the input and marks held/live routes. MRP does not take over that job:
it rereads after `Land(ⁿB)` and asks whether the landing produced an additional resultant burden
beyond the initial inventory.

## No Premature STOP

Core recursive traversal rule: no premature STOP while an eligible live burden remains.

An eligible live burden is a same-input distortion, held route, or downstream burden that was already
present in the original input and becomes releasable after the current blocker clears. STOP is
invalid merely because the first strong move landed. If another eligible live burden remains, choose
RECURSE for the next bounded pass or PARTIAL when limits prevent that pass.

STOP is valid only when state re-read confirms:

- the current blocker cleared,
- no eligible live burden already present in the original input remains live,
- no held route became releasable,
- continuing would be argument-stacking rather than governed traversal, and
- P7 permits stopping.

## Same-Response RECURSE

Same-response recursion is an internal state-transition, not a user-reply requirement. It is
required when the gate confirms this same-response RECURSE trigger checklist:

1. Current blocker cleared.
2. Another already-present burden remains live.
3. The next pass has a present release signal.
4. No P7 stop, register-hold, semantic gate, thin-basis rule, absent release signal, or limit
   blocks release.

When all four conditions hold, RECURSE is required in the same response. When the next pass is
eligible but limits prevent it, use PARTIAL. When the next pass remains live but its release signal
is absent, use HOLD. STOP is invalid.

This is `held_burden_activation` when the next burden was already in the initial Layer A burden
inventory. It may be MRP-authorized as a route, but it is not an MRP-generated burden.

**NewB license test:**

`NewB` is licensed only when state re-read can show all seven facts:

1. the prior `B` landed through owner-specific operation, not merely through section shape;
2. the cumulative-state delta is explicit enough to show what changed;
3. the proposed next burden was already present in the original input, prior held material,
   or the collapse radius of the prior burden;
4. the proposed next burden differs from the prior `B` by target-family, claim-level,
   restoration vector, or governing noetic pressure;
5. the proposed next burden was not already answered as an operative submove;
6. the route-gradient `∇` after `Land(B) -> R(H,Δ)` points to that burden rather than to STOP,
   HOLD, LoopBreak, or duplicate/derivative collapse;
7. release is not blocked by stop, register, semantic, thin-basis, source-use, or limit gates.

If any fact is missing, the next material is not NewB. It remains an operative submove,
HOLD, or PARTIAL.

**MRP-generated resultant burden test:**

An MRP-generated burden is a narrower category than ordinary `NewB`. It is licensed only when
`MRP(ⁿB)` can show all seven facts:

1. `ⁿB` landed or partially landed through owner-specific operation;
2. `R(H,Δ)` detected pressure not fully present in the initial Layer A inventory;
3. the renewed route-gradient `∇` points to that pressure after reading `ΔⁿB`, `Δκ`,
   `∇·B`, `∇×κ`, `ξ`, `Ω`, concealment/framework pressure, and held routes;
4. the pressure is graph-bound, commitment-bound, framework-bound, or grounded in the prior burden's
   collapse radius, not speculative topic expansion;
5. the new node differs from `ⁿB` and from already-held burdens by target-family, claim-level,
   restoration vector, or governing noetic pressure;
6. the new node is not merely an operative submove already answered inside `ⁿB`;
7. MRP records `MRP route result type: generated_burden_instantiation`, graph/provenance
   `ⁿB → ⁿ⁺¹B`, and route `RECURSE` or `HOLD`;
8. the output instantiates `ⁿ⁺¹B [generated-by: MRP(ⁿB)]` as a normal burden node with Layer A
   accounting, Layer B governed operation body, owner-bearing submoves, and `Land(ⁿ⁺¹B)` or
   `HOLD(ⁿ⁺¹B)` before closure is licensed.
9. if the generated node is high-mass, its owner-bearing submoves are operation-shaped rather than
   conclusion-shaped: they identify the exact claim, pressure, route, predicate, source-status,
   consequence, or affective/noetic move being worked; explain why it is live after the prior
   landing; apply the named owner/TTP; produce a concrete state delta; and connect that delta to
   `Land(ⁿ⁺¹B)`. FPD exposes an imported premise or criterion, M8 traces consequences, M9 repairs
   predication/category structure, source-status or authority-order repair sorts authority and
   hidden support, P7 bounds stop/reopen conditions, and LoopBreak exits circularity. A generated
   node does not land merely because it has two submove labels or because its body states the
   intended conclusion.

If the proposed node was already present in the initial inventory, the route result type is
`held_burden_activation`, not `generated_burden_instantiation`. If no additional resultant exists,
record `no_new_resultant` and continue ordinary route/closure discipline.
The formal difference is load-bearing: held activation means `R(H,Δ)` found the route-gradient
pointing to a node already carried in `H` / the initial set; generation means `ΔⁿB` exposed a
new `ξ`, `Ω`, concealment, dependency, or burden-gradient pressure that was not fully inventoried.
STOP means `∇·B` is neutral, `∇×κ` is null/resolved, no remaining `∇` points toward an
input-anchored burden in licensed scope, live `ξ` / `Ω` / concealment pressure is accounted for
or bounded, `𝒞(Ψᴺ)` is satisfied, and `T_lang` remains a boundary rather than uptake.
The same distinction applies in the `Closure/Reconstruction Witness` `MRP resultants` ledger:
do not repair a missing visible route-type line by calling an already-initialized held node
`generated_burden_instantiation`. For an inventory such as `[¹B, ²B, ³B]`, `MRP(¹B)` with
`graph=¹B → ²B` is a held activation unless `²B` first appears after the post-landing reread and
is rendered as `²B [generated-by: MRP(¹B)]`.

Practical/application material is not NewB merely because it needs its own heading. Source
maps, concise answer wording, "how to respond" sections, do/don't guardrails, warning
paragraphs, and recaps of already-landed material belong in the current Layer B, the final
Restorative/Application Response, or Closing Formulation unless the state re-read proves a
distinct unresolved noetic function. Across case families, test the proposed new burden by
function, not by topic: naturalist evidence criteria, testimony/tawatur pressure,
predication/category pressure, divine-plurality/person-nature or tradition-specific coherence
pressure, kalam/falsafah proof-method pressure, grief/register HOLD, authority fatigue,
source-worldview transfer, moral protest, hiddenness, and worship-worthiness may each become a
burden only when they remain
input-anchored and unresolved after `Land(B) -> R(H,Delta)`. Source-worldview is allowed as a
separate burden when the worldview/source-frame itself is criterion-bearing or explicitly
requested for dismantling; practical response guidance is not automatically a burden.

Default Final-Output Preflight Gate must enforce this decision. It is not merely a
visible-format sanitizer. After the first bounded move, final-output preflight asks:

- what cleared?
- what remains live?
- was the remaining live burden already present in the original input?
- did `MRP(ⁿB)` generate any additional resultant burden beyond the initial inventory?
- is it now eligible?
- is any stop/register/semantic/thin-basis gate blocking it?

If another eligible same-input live burden remains after the current blocker clears, default
output must internally license recursion and continue with one bounded next pass using a prose
state transition, or render a partial release-status reason in prose if limits prevent doing so.
It may not silently close while an eligible burden remains. Clean prose without this state re-read
and internal STOP / HOLD / RECURSE / PARTIAL decision is still invalid.

This decision is not satisfied by a preplanned essay sequence. Headings such as "Step 1",
"Step 2", "Step 3", "Step 4", "Move 1", "Move 2", or "Move 3" do not show state re-read.
Same-response RECURSE requires: the
first bounded move landed, the state re-readed, the next live burden was already present in
the original input, the gate permits release, the next pass is bounded, and the next pass
refreshes state again before any further release.

## Hold And Release Semantics

Held means traversal-delayed, not response-delayed. Held also means traversal-delayed, not
permanently suppressed.

Holding downstream material is not a promise to wait for another user message. After a bounded
move lands, state re-read must recheck held routes. If a previously held route becomes eligible
and no stop or gate blocks it, it becomes the next bounded pass. If it remains blocked, HOLD is
valid and the blocker must be named.

## Recursion Discipline

Recursion is not argument dump. It is one live burden per burden-cycle: upstream before downstream, current-pass
modules only, state re-read after each move, and no total downstream release at one refresh.

No module stacking is permitted without a prose state-change transition. A visible response may
compress the audit surface, but internally it must still pass through a bounded move, state re-read,
and a renewed decision before releasing the next live burden.

Default mode may compress that transition into ordinary prose, but it may not hide it. A
valid default transition says what cleared, what remains live, why the next live burden is now
eligible, and why continuation rather than prose closure, hold, or partial traversal is licensed.

Default governed prose follows the mandatory compact DSL/IR header + Layer B + State/noetic
re-read burden-cycle shape in `diagnostic-render-contract.md`, then repeats only until governed
recursive sufficiency.

Default mode must not print literal state fields such as `Recursion decision:`,
`next_eligible_pass:`, `post_render_gate:`, `Governance:`, or STOP / HOLD / RECURSE / PARTIAL
as a visible governance label. Literal state labels and post-render fields are for `:dsl`,
internal/development audit, pass-review, or diagnostic trace. Default continuation is valid
only when the answer visibly performs the transition and the one bounded next pass; naming the
decision is not execution.

### Minimum Visible Transition Spine

Default mode suppresses raw visible IR but does not suppress recursive execution.

**Formal terminology:** Use final runtime terms, not debugging shorthand.
- Live noetic burden: the input-anchored claim, criterion, structural pressure, or noetic feature currently being cleared.
- Operative submove: a TTP operation inside the current live noetic burden.
- Burden-cycle: one Layer A -> Layer B -> state re-read traversal of a live noetic burden.
- Burden landed: the current live noetic burden has produced a result sufficient for re-reading state.
- Next live burden: another input-anchored burden licensed after re-read.
- State re-read / noetic re-read: the post-burden reassessment after the current burden lands.

A live noetic burden is not a topic count. Use the canonical invariant:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
Gloss: the current `B` may require several `s` before `Land(B)`; recursion waits for `R`.
Anchor wording: the current live noetic burden may require several operative submoves.
Operative submoves are not burden-cycles. Live-burden boundary is set by the noetic burden being
cleared, not by the count of TTP names or visible headings.
Burden completeness rule: once `B` is released, materially necessary sub-burdens inside that
same `B` must receive matched TTP/operator treatment before `R`. Do not answer only the headline
objection, skip internal sub-burdens, replace routed execution with generic prose, or jump to a
broad conclusion. `R` may then expose deeper governing epistemology as `NewB`, first-order
repairs, held higher-order rebuttals, or STOP/HOLD/PARTIAL/RECURSE; `NewB` is not licensed until
the released `B` and its necessary `s` have actually been operated on.
The execution bias is toward exhausting input-anchored live structure, not minimizing it. Address
as many released burdens and materially active submoves as the gates permit; do not consolidate
distinct active operator functions into a shorter generic response. If the model cannot finish
the remaining live structure in the current response, the correct state is PARTIAL with the next
live burden and blocked submove(s) named.

In moral-protest / hiddenness / worship-worthiness cases, imported-criterion testing,
hujjah/accountability correction, punishment narrowing, guidance-as-coercive-proof correction,
named source-worldview source-status discipline, and identity-stabilization caution are `s`
only when the state gate proves they share the same target-family, claim-level,
source/noetic frame, claim cluster, and restoration vector. They must remain distinct
operative submoves with their own target -> operation -> result; same `B` does not mean
collapsed prose. In hard compound source-request cases, do not presume these functions all
serve the first tribunal burden merely because they support the same final indictment. They
become later burden-cycles if `R` licenses a genuinely new input-anchored `B`, including a
distinct claim-level, source/noetic frame, theological target, or restoration vector that was
not fully landed as `s`.
When the user's input publicly anchors a worldview or identity frame and that frame supplies
the moral criterion, authority-order, discourse posture, or restoration vector, it is not merely
biographical source-status. It remains operative until consequence trace, source-status
discipline, and restoration/practitioner implication have landed or have been explicitly held.
Keep motive and soul-state held; do not drop the burden.

Multi-burden does not mean multi-recursion by default. The model must not split topical components
into new burden-cycles merely because they name hiddenness, punishment, source-status,
source-worldview, or identity-stabilization.
Opposite guard: do not overcollapse distinct input-anchored burden families into one first
tribunal or one broad answer. Same-burden collapse is licensed only when `Sameτ`,
`SameSourceFrame`, `SameClaimCluster`, and `¬NewB` actually hold. If accountability compression,
hiddenness/coercive-guidance pressure, punishment/mercy/justice architecture, source-worldview
consequence, predication, transmission/testimony, grief/register, or family-local proof-method
pressure carries a distinct target/function/restoration vector, `R(H,Delta)` must release it as
the next `B`, HOLD/PARTIAL it with reason, or mark a runtime limit. Dense hard cases may require
extensive output; short closure with remaining live burden is invalid.
Burden recursion follows noetic order, not topic count. A first-order burden is the surface
claim or objection. A second-order burden is the criterion, warrant, proof-method,
source-authority, testimony standard, moral tribunal, or epistemic rule judging that claim. A
higher-order/meta-noetic burden is the governing source-worldview, autonomy/desire authority,
identity-protective discourse, inherited default, grief/register pressure, source-status
inversion, or noetic-frame collapse. If `R(H,Delta)` shows a different order remains live, the
next `B` is licensed; if it shows only more content inside the same order/function/source-frame,
keep it as `s`, application, HOLD, or PARTIAL.
Reason for the rule: the skill protects noetic function, reliable warrant-process, and
foundational order. It asks what is functioning as basic, what is inferred, whether the
claim-assessing process is truth-conducive, and whether the noetic operation is deformed by
hawā, inherited assumptions, identity pressure, grief, source inversion, desire, imported
tribunal, selective testimony rule, scientistic filter, anti-revelation prior, or self-authorizing
moral standard.
The user's practical request to respond, deal with a claim, bring sources, or dismantle a belief
system does not itself license a late practical-handling `B`. It requires source-operation inside
the relevant burden-cycles and final Restorative/Application Response. Practical handling becomes
`B` only when a distinct practitioner constraint remains live after `Land(B) -> R(H,Delta)`.
Forbidden failure name: topical components split into burden-cycles without a state/noetic re-read.
Opposite failure name: topical components consolidated into one generic submove.
Short form: hiddenness/punishment/source-status can be operative submoves under one burden only
after same-function proof; otherwise `R(H,Delta)` releases, HOLDS, or PARTIALs them as distinct
burdens. In either case, each active TTP/operator remains a distinct `s` or later `B`.
Same-burden collapse preserves TTP/operator identity: each materially active `s` must show why
that operator is live for the current `B`, its target, its operation, its result/state change,
and how the result contributes to `Land(B)`. Imported-criterion pressure keeps FPD-style
criterion-import detection visible; self-grounding or self-defeating criteria keep M1/M1P-style
pressure visible; worldview consequences keep M8-style reductio visible; divine-predicate
errors keep M9/predication discipline visible; reason-role repair keeps V2 visible; restoration
and stop discipline keep P1/P7 visible; transmission, predication, grief/register, and
family-local proof-method pressures keep their relevant owner/TTP identity where active.
Bad split pattern: imported tribunal / hiddenness / punishment / named source-worldview without
state-re-read licensing.
Bad collapse pattern: imported tribunal answer that names hiddenness, accountability,
source-worldview, or identity-stabilization but does not execute each active function as a
separate target -> operation -> result submove or later burden.

Recursion begins only when `Land(B) -> R` licenses a new input-anchored live burden that remains
after the submoves have done their work. If the facet has already been handled as `s`, it cannot
be promoted into the next cycle just to create serial depth.
If the facet has not been materially handled as a distinct `s`, it has not been handled.
Do not count a label, route-code mention, or compressed sentence as a landed submove.
Anchor wording: Recursion begins only when the current gated operation lands.
Equivalent legacy wording: Recursion begins only after that burden lands, the state is re-read,
and another input-anchored burden is licensed.

A route chain is not a bounded operator. `FPD -> M1 -> DO-8 -> M8 -> restoration` is a route itinerary,
not a current live noetic burden. Current bounded operator names one burden-level function such as
`imported moral tribunal / worship-worthiness criterion burden`. Smaller phrases such as
`hujjah/accountability correction` or `guidance-as-coercive-proof correction` are operative
submoves only when they merely test or narrow that same burden. When the input anchors
accountability/hujjah or hiddenness/coercive-guidance as its own noetic function,
`R(H,Delta)` must release it as a next burden, HOLD/PARTIAL it, or state why the
same-function gate kept it inside the current `B`.
hujjah/accountability correction can be an operative submove after same-function proof.
guidance-as-coercive-proof correction can be an operative submove after same-function proof.

**Recursion defined (for default mode):**
```text
topic transition != recursion
component tour   != recursion
burden landed -> state re-read -> next input-anchored live burden -> next burden-cycle
```

State re-read enumeration of remaining input-anchored live burdens plus one newly routed bounded pass per refresh = recursion. A TTP's visible execution spine is:
target -> operation -> result -> state re-read.

A recursive response must:
1. Land the governing live noetic burden in the current burden-cycle.
2. Run state re-read / noetic re-read.
3. Enumerate remaining already-present live burdens from the original input.
4. Route one bounded live burden per burden-cycle; a burden may contain multiple operative submoves,
   and every materially active submove receives its own target -> operation -> result.
5. After each burden-cycle, re-read state again and enumerate remaining burdens.
6. STOP only after proving no input-anchored eligible burden remains, or remaining burdens are
   HELD with release conditions, or limits force PARTIAL with the next live burden named.

The transition spine must mark state re-read, not topical movement. Each transition must show:
(1) what the prior burden landed, including operative submove results, (2) what input-anchored
live burden the noetic re-read identified as remaining, and (3) what the next burden-level
function is. If no transition marker appears when re-read licenses another input-anchored live
burden, the output is clean essay surface-compliance failure and must be rewritten before emission.

Valid internal progression for the first live burden:
"The same tribunal test has three operative submoves. First, the secular moral criterion has to
justify its authority. Second, the accusation that Islam punishes mere non-belief has to be
narrowed through hujjah/accountability. Third, hiddenness has to be corrected where it assumes
coercive individualized proof. These submoves serve one burden: whether the imported criterion
has authority to declare God unworthy of worship."

Valid transition to a new burden:
"That burden has landed: The imported criterion no longer governs as judge; the imported
tribunal no longer stands as an unquestioned judge over divine action. What remains live
is a different noetic aspect: the foundational epistemology by which moral and evidential
standards claim authority at all. That is the next live burden."

Invalid default-mode recursion shapes:
- "Step 1 / Step 2 / Step 3" as fake recursion.
- "Move 1 / Move 2 / Move 3" as fake recursion.
- "Pass 1 / Pass 2 / Pass 3" used for FPD, M1, DO-8, M8, or restoration fragments inside one burden.
- "Pass 1 / Pass 2 / Pass 3" used for imported criterion, hujjah/accountability, and
  guidance-as-coercive-proof corrections before state re-read proves whether they are
  same-function submoves or distinct input-anchored burdens.
- "Burden 1 / Burden 2 / Burden 3 / Burden 4" used for imported tribunal, hiddenness,
  punishment, and named source-worldview without a state/noetic re-read proving that each is a
  new live burden rather than a subordinate submove under the same tribunal burden.
- One imported-tribunal burden that mentions hiddenness, punishment/accountability, consequence
  tracing, source-worldview, or identity-stabilization without rendering them as distinct
  operative submoves when they are active.
- `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`.
- silently stopping after criterion correction when another eligible live burden remains.
- restoration synthesis or pastoral note before the active burden lands and state is re-read.

TTP labels do not satisfy execution. A valid default burden-cycle must show the bounded target,
operation performed, result of the operation, and burden landing before any next burden-cycle.
In short:

```text
live noetic burden -> operative submove(s): target -> operation -> result -> burden landed -> state re-read
```

State re-read follows the burden landing, not each route label in a preplanned itinerary. If the
same imported tribunal remains the live target after same-function proof, FPD, M1, DO-8, M8,
hujjah/accountability correction, guidance-as-coercive-proof correction, and
identity/source-status clarification remain operative submoves under the first live burden.
They are not burden-cycles until state re-read licenses a new input-anchored noetic aspect.
If the hard input separately anchors those pressures, they must not be collapsed into the
tribunal burden without that proof.
TTPs execute across refreshed case-states, not as a one-time itinerary from the initial read.
The initial case-state selects only the current bounded operator. Once that operator lands,
state re-read re-evaluates upstream/downstream, higher-order/first-order, and held material
already present in the same input. The next TTP, if any, must be selected from that refreshed
state. Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future
contingencies stay held with a release condition.

Length is governed by burden-cycle live-burden traversal: bounded pass, state re-read, next
eligible same-input burden, bounded pass, refresh again, then STOP, HOLD, RECURSE, or PARTIAL.
Do not compress default output into premature STOP merely to keep it short.
Extensive output is required when the live noetic structure requires extensive traversal; no
live burden, active TTP, source function, family distinction, held-route re-read, or restoration
vector may be omitted merely to keep the response below an implicit size ceiling. If limits prevent
full traversal, the correct state is PARTIAL with the named next burden or blocked submove.
PARTIAL requires concrete limit reason: name the live burden and the response/tool/interaction
limit preventing traversal. A bare PARTIAL label is not a release decision.

Positive target: governed recursive sufficiency. Recursion continues until the live same-input
noetic structure has been restored as far as the input and release gates permit: case-state read,
governing live burden, bounded TTP operation, result, state re-read, then the next eligible live
burden or HOLD/PARTIAL/STOP.

This is the recursive-state form of `anti-patterns.md` Route Surface-Compliance Failure Failure: visible
recursion label != recursive traversal; pass-by-pass state re-read = recursive traversal.
It is also the recursive-state guard against Clean Essay Surface-Compliance Failure: every pass must show a
transition before the next bounded operator starts.

Compact audit shape when recursion must be visible in `:dsl`, internal/development audit, pass-review, or
diagnostic trace:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded move:
state re-read:
Release status: prose closure/hold/partial/continuation status; no literal STOP/HOLD/RECURSE/PARTIAL label
```

## Grounded Noetic Re-Read Shape

State re-read / noetic re-read is not satisfied by field-shape alone. The block must be
grounded in the preceding burden-cycle. This file owns the auditability rules.

The minimum grounded noetic re-read shape, when no canonical block already governs the
render, is:

```text
Noetic re-read:
- burden landed:
- still live:
- held:
- recursion decision:
- next licensed live burden:
```

This shape introduces no new IR fields. It is a render-time rephrasing of the existing
post-render gate fields (`cleared_this_pass`, `remaining_live_distortions`,
`held_routes_rechecked`, `recursion_decision`, `next_eligible_pass`).

**Field-grounding rules (mandatory; checker-enforced):**

1. `burden landed` must be traceable to the immediately preceding burden-cycle's burden
   result. A `burden landed: yes` claim that follows no operative submove producing a
   `target -> operation -> result` chain is a formatted but ungrounded noetic re-read and
   must be rejected. The Layer B above the re-read must contain at least one operative
   submove whose result feeds the burden landing.
2. `still live` must enumerate items already present in the original input, in held
   material from prior burden-cycles, or in a load-bearing dependency whose support
   collapsed when this burden landed. A `still live` entry that introduces material not
   anchored in those sources is unanchored introduction; the entry is invalid.
3. `held` must name material that was already named as held in a prior Layer A or whose
   release signal is currently absent. Treating a previously released item as held is
   regression and must be rejected.
4. `recursion decision` (`STOP | HOLD | RECURSE | PARTIAL`) must be consistent with
   `burden landed`, `still live`, and `held`:
   - `STOP` requires `still live: none` (or all entries explicitly held with absent
     release signal) and no held route newly eligible.
   - `HOLD` requires at least one named blocker for each remaining `still live` item.
   - `RECURSE` requires at least one item in `still live` for which release is now
     permitted.
   - `PARTIAL` requires a concrete limit reason and a named next licensed live burden.
5. `next licensed live burden` must be anchored in `still live`, in held material whose
   release signal has now appeared, or in the original input. It must not appear from
   nowhere. If `recursion decision` is `STOP` or `HOLD`, this field is `none` or names
   what would be released on a future refresh.
6. A new burden-cycle may begin only after a noetic re-read whose `burden landed` is
   grounded by rule 1 and whose `next licensed live burden` is grounded by rule 5.
   Beginning a new burden-cycle from a re-read block alone, without a prior operative
   result, is invalid.
7. `state delta` / cumulative-state delta must be known even when not printed as a raw
   field in default mode: the response must show what changed, what narrowed, and why the
   next burden is different from the burden just landed. A re-read that merely repeats
   "cleared / held / decision" without a changed claim-state is rubric-schematic and invalid.

**Failure conditions:**

- `burden landed: yes` asserted without an operative-submove `target -> operation -> result`
  in the immediately preceding Layer B.
- `still live` lists a topic not present in the original input, prior held material, or the
  preceding burden-cycle's collapse radius.
- `next licensed live burden` is asserted but `still live` does not contain it and held
  material does not contain it.
- `recursion decision: STOP` while `still live` is non-empty without explicit HOLD reasons.
- `recursion decision: RECURSE` while `still live` is empty.
- A new burden-cycle begins after a re-read whose `burden landed` is asserted but not
  produced through an auditable operative submove.
- A new burden-cycle begins after the prior re-read fails the NewB license test.
- A burden-cycle exceeds three major operative submoves without the submove saturation gate.
- A TTP is named and paired with generic prose but does not satisfy the owner-specific
  operation floor.
- A noetic re-read provides a decision but no cumulative-state delta.

These conditions are auditable by source review; the checker enforces a representative
subset of them on structural fixtures.

The grounded shape is render-mode-agnostic. Default mode renders the same content under
`State/noetic re-read` without raw post-render gate fields. `:dsl` / internal/development
audit may surface the field block. In every mode, the grounding rules apply.

## Source-Status & Noetic-Frame Non-Equivalence Discipline

This section is canonical for source-status discipline and noetic-frame non-equivalence.
It governs how sources are used inside burden-cycles. It introduces no new routes, IR
fields, or module owners; it formalizes existing requirements.

**Thesis-protection rule.** The notation layer above is canonical: `N_AT` aliases the
Atharī/Taymiyyan/Salafī/Wahhābī operative frame for repo routing, while
`N_Ashʿarī[*]` and `N_Māturīdī[*]` are family labels, not automatic operative `N`.
Umbrella terms such as `classical theology`, `classical theologies`, `classical Islamic
theology`, `the classical tradition`, `mainstream kalām`, or `Ashʿarī/Māturīdī tradition`
must not flatten rival frames into one operative authority. The rule applies inter-school
and intra-school: `family label != operative N`; `shared vocabulary != shared warrant`.

**Source-status taxonomy.** Every source used in a burden-cycle is marked with one of
the following statuses; a source may appear in only one status per burden-cycle:

```text
operative support     - the source is being used as warrant for the operative conclusion
contrast              - the source is named to mark a differing noetic structure
opponent-position     - the source is named as the position being engaged
historical note       - the source is named as historical or genealogical context
genealogy             - the source is named as the genealogy of a dispute
held material         - the source is named as held by routing/release governance
bounded comparison    - the source is named under an explicit bounded comparison
```

**Source-status non-equivalence rule.** A source marked as `contrast`, `opponent-position`,
`historical note`, `genealogy`, `held material`, or `bounded comparison` must not be used
as `operative support` in the same burden-cycle unless explicitly reclassified with a
named justification: a sentence stating the reclassification, the reason, and why the
selected operative noetic frame is preserved. Cross-frame prestige stacking (citing
contradictory schools side-by-side as one authority) is forbidden in every mode.

**Default public-render source restriction.** In default output, school, author, citation,
genealogy, external philosopher, theologian, framework, or contextual-source references are
not public-render material unless the user explicitly asks for them or validated IR
specifically requires source-comparison. Default citation allowance is restricted to Qurʾān,
Sunnah, and sound narrations from the Salaf; if any of these are used, each must be directly
referenced through an external source. Do not use named scholars, named schools, external
philosophers, external theorists, or contextual authority labels as public-render support in
default mode. Do not use `Wahhābī` as default public terminology unless the user's input
uses it and the label itself must be clarified.

Controlled scholarship labels: in operative source-status fields, reserve `Islamic scholar`
and `Islamic scholarship` for Salafī/Atharī-aligned scholarship; do not use them as umbrella
warrant labels. For Ashʿarī, Māturīdī, Muʿtazilī, kalām, or falsafah figures, use labels such as
`kalām theologian`, `speculative theologian`, `school theologian`, `mutakallim`,
`philosopher`, or `later theological figure`. This is noetic-frame control, not public
denunciation or scholar/source parade.

**Method-source non-branding rule.** The framework is not publicly framed as belonging to,
deriving from, or being branded under a named scholar, named school, newly coined methodology,
new creed, new ʿaqīdah, or new noetics. Public/default framing remains sound noetic diagnosis
-> detection of deformation/concealment/criterion import -> restoration of proper
warrant/order and proper cognitive function in a congenial epistemic milieu. Methodological
consonance may be preserved internally without source-branding.

**Operative-frame selection rule.** Each burden-cycle proceeds from one selected
operative noetic frame. Other frames may be named only under non-operative statuses.
The selected frame must be visibly identified when source-status discrimination would
otherwise be ambiguous; phrases such as `the classical tradition agrees` or
`Islamic tradition says` are forbidden when the claim is school-sensitive or disputed.

## Source-Status Child Modes

These are child modes of this source-status / noetic-frame discipline, not standalone
owners. `nomenclature-normalization.md` governs label naming, `noetic-reading-checklist.md`
governs operative-N caution, `inference-boundary.md` governs source-status markers across
loaded files, and `foreign-premise-detection.md` owns imported-tribunal detection. This table
owns the local source-status operation when a label, source, affiliation, statement, person,
or quote packet is trying to carry warrant before its function has been typed.

| mode_id | entry criterion | false trigger | target | operation | result | Land(B) effect | R(H,Delta)/kappa effect | heart/register consequence | deformation release condition | source-worldview / tribunal consequence | held route | smoke link |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AS-2 school-label identity audit | A school, family, source, or identity label is used as warrant, proof, noetic-state lock, identity verdict, or public authority signal. | The label is merely biographical, historical, or explicitly bounded and is not governing the burden. | The school/source/identity label and the warrant-function it is being made to perform. | audit whether the label is functioning as identity signal, source-status context, operative warrant, or noetic-state lock. | The label is demoted, bounded, or reclassified; family label is not operative warrant, so the route returns to operative doctrine, explicit claim, proof rule, or source-status evidence. | The burden lands when the label no longer decides the claim by identity/prestige. | Reread NS, source-status, proof-method, and downstream authority claims that depended on the label. | If unity, shame, public affiliation, or identity-cost pressure is live, bound release and avoid polemical labeling. | If taqlid, inherited framework, zann, or identity-performance is live, M5/V1 must release the source-status burden before AS execution becomes public content. | If the label installs a tribunal or authority-order inversion, hand upstream to FPD/V2/source-status before ordinary content. | School profile, doctrinal content, public verdict, or proof-method route remains held until the label's function is typed. | as-school-label-identity-audit |
| AS-3 conscious doctrine vs inherited affiliation split | An affiliation, family label, majority identity, public community label, or inherited association is treated as conscious doctrine or operative creed. | The person/source explicitly states the doctrine, method, and proof rule at issue. | The relation between affiliation, conscious commitment, operative doctrine, and actual noetic operation. | distinguish inherited affiliation, public identity, explicit doctrine, and operative noetic rule. | The case remains provisional, composite, or unknown-pattern-typed; operative doctrine remains provisional unless anchored. | The burden lands when affiliation no longer substitutes for doctrine. | Reread NS selection, profile confidence, AS-2, proof-method, and public-authority routes. | If identity-cost or unity pressure is live, bound language and avoid turning the split into public denunciation. | If taqlid or inherited framework is live, mark affiliation as stabilizer, not proof of conscious doctrine. | If affiliation is being used to grant tribunal authority, hold content pending FPD/source-status. | School-specific content and public verdict remain held until operative doctrine is anchored. | as-affiliation-doctrine-split |
| AS-4 statement/person/method distinction | A statement, error, method, person, group, public use, or school is being collapsed into one verdict. | The burden is only about one explicitly bounded statement and does not imply person/method/source-status classification. | The attribution locus: statement, person, method, public use, source posture, or noetic rule. | distinguish statement, person, method, public use, and source-status function before assigning severity or downstream consequence. | The verdict is narrowed to the correct locus; person-level and method-level claims remain held unless separately grounded. | The burden lands when the attribution locus is typed and over-attribution is blocked. | Reread deviation, takfir, source-status, public-use, and collapse-radius routes. | If public polemic, shame, or community identity pressure is live, bound output and avoid rhetorical escalation. | If hawa/gharad/identity-performance or zann is live, hold person-level extension unless anchored. | If the method itself installs a tribunal, hand to FPD/V2; if the statement is only local error, keep it local. | Person verdict, method verdict, public warning, and school-level conclusion remain held until the locus is proven. | as-statement-person-method-distinction |
| AS-8 source as evidence vs source as identity signal | A quote, scholar name, school label, source stack, citation, bibliography, or authority marker is used ambiguously as evidence, prestige signal, identity signal, contrast, genealogy, or bounded comparison. | The source is explicitly cited for a bounded proposition and its status/weight is clear. | The source-use function. | classify the source as evidence, contrast, genealogy, identity signal, prestige signal, held material, or bounded comparison; then determine whether it can carry the current claim. | Source-use is reclassified before content release; argument-bank or source-parade release is blocked. | The burden lands when source function and weight are typed before content release. | Reread proof-method, authority-order, source-status, and downstream claim support. | If public prestige, shame, affiliation, or authority fatigue is live, bound source use and avoid source parade. | If taqlid, inherited framework, or zann is live, source stack may be a stabilizer rather than evidence. | If a source stack installs academic method, school prestige, or external authority as tribunal, hand upstream to FPD/V2/source-status. | Content claim, public verdict, source-stack summary, or school profile remains held until source function is typed. | as-source-evidence-identity-signal |

**Cited-agreement rule.** When agreement across frames is asserted, the response must
mark whether the agreement is substantive (the structural conclusion holds in each frame
on each frame's own grounds) or merely verbal/surface-level (the words coincide while
the operative grounding differs). Verbal agreement is not operative support.

**Failure conditions:**

- An umbrella term flattens contradictory schools into one authority.
- A contrast-marked source is then used as operative warrant in the same burden-cycle
  without explicit reclassification.
- A burden-cycle cites Ashʿarī or kalāmic authorities as operative support for a
  Taymiyyan / Atharī operative conclusion (or vice versa) without source-status marking.
- A response asserts `the classical tradition agrees` for a school-sensitive claim.
- A response asserts agreement across frames without marking substantive vs. verbal.
- `N_AT` aliases are counted as four independent authorities or separate warrants.
- `N_Ashʿarī[*]` or `N_Māturīdī[*]` is used as operative support without the selected
  live predicate/warrant/criterion/authority-order.
- Shared vocabulary or shared conclusion is treated as shared warrant.
- Identity-frame is treated as operative support for a content claim without
  source-status caution.

**Operative-warrant sentence convention.** When any non-operative source (`contrast`,
`opponent-position`, `historical note`, `genealogy`, `held material`, `bounded comparison`)
is named in `:dsl`, internal/development audit, pass-review, diagnostic trace, or an
IR-required source-comparison render, that rendered source-status block must include one
prose sentence in this minimum shape:

```text
Operative warrant: [selected operative noetic frame]; the [contrast | opponent-position
| historical | genealogy | held | bounded-comparison] source above does not contribute
to this warrant; specifically, [named element from the non-operative frame] is not used
as a premise here.
```

The final clause is the specific non-premise clause. This adds no new IR field. It converts the implicit operative dependence into an
explicit claim that can be audited. A burden-cycle that names a non-operative source
without this sentence is at risk of source-status label-emission without substantive
discrimination: the label emits compliance while the operative reasoning silently relies
on the contrast frame's content. The convention is normally not public default material; it is expected
in `:dsl` / internal/development audit, and is the canonical disambiguator when a reviewer needs to verify
that the contrast was held to its named status.

**Allowed shapes:**

- `Source-status: operative support. The selected operative frame is X; the conclusion
  holds inside that frame.`
- `Source-status: operative support. Selected frame: N_AT; alias labels are not counted
  as multiple warrants.`
- `Source-status: contrast only. This Ashʿarī formulation is named only to mark a
  differing noetic structure. It is not used as warrant for the operative conclusion.`
- `Source-status: historical note. Some later kalāmic treatments frame the issue
  differently; this is not the operative authority for this burden-cycle.`
- `Source-status: bounded comparison. The Māturīdī and Taymiyyan framings agree
  verbally that X, but the operative grounding differs; the operative warrant in this
  burden-cycle is the selected frame only.`
- `Operative warrant: selected Atharī predication frame; the contrast source above does
  not contribute to this warrant; specifically, the later kalāmic formulation is not
  used as a premise here.`

**Forbidden shapes:**

- `Classical Islamic theologies, including Ashʿarī, Māturīdī, and Taymiyyan approaches,
  all provide acceptable ways to ground the answer.`
- `The whole classical tradition agrees that ...`
- `Ashʿarī theology teaches X` when the point is internally disputed within Ashʿarī or
  is school-sensitive across kalāmic and Atharī frames.
- `Māturīdī theology teaches X` under the same conditions.
- `Islamic tradition says X` where the claim is school-sensitive and structurally
  disputed.
- A list of sources hides disagreement behind breadth.
- `Ashʿarī, Māturīdī, and Taymiyyan approaches are all classically acceptable theological
  routes here.`
- `Atharī, Taymiyyan, Salafī, and Wahhābī ʿaqīdah are four independent authorities here.`
- A contrast-marked source is named, then immediately used as evidence for the operative
  conclusion in the next sentence under the same burden-cycle.
- `This is the daee-epistemics method of [named scholar/school]`, `a new ʿaqīdah/noetics`,
  or any authority-by-association method branding.
- Default output uses named scholars, named schools, external theorists, genealogy, or
  school-label context as support without explicit user request or validated
  source-comparison IR.

These failures are not citation-style errors. They are thesis-protection failures: the
skill's diagnostic compiler must discriminate noetic structures, not flatten them.

## State Carry / Reset / Re-Evaluation Table

This is the canonical State Carry Table for the abstract refresh operation.

| State component | Carry rule |
|----------------|------------|
| NS code, deformation, concealment mode, DO-orient | Carried: stable diagnostic read persists until a fresh differentiating signal changes it |
| Restoration target | Carried if still unmet; updated if the landed move partially resolved it |
| Alignment state, Recognition strength | Carried as progress state; these do not reset merely because a pass ended |
| What remains live | Carried as the live input to the next V1 opening |
| Held routes / What is withheld and why | Carried across burden-cycles as a coherent set; never silently dropped |
| Matched modules | Reset: re-derived from refreshed state; not inherited from the prior pass |
| Layer B content | Reset: re-derived from refreshed state |
| Next move | Reset: one live move only; never a queue |
| Continuation eligibility | Re-evaluated fresh from the refreshed state; not inherited from the prior pass |

**Held-routes carry rule (cross-cycle).** Burden-cycle N's Layer A `Held routes` field
must be derivable from:

```text
Held(N) = (Held(N-1)) ∪ (input-anchored burdens not yet released) − (items released by Burden N-1)
```

New material introduced in Burden N's `Held routes` must be anchored in the original
input or in a load-bearing collapse-radius dependency that became visible when Burden
N-1 landed; it must not appear from nowhere. An item silently dropped from Burden N's
`Held routes` (without an explicit release event in Burden N-1's state re-read) is
held-material amnesia: the recursion has lost state, and the meta-noetic memetics
claim that the DSL/IR tracks live noetic state across the conversation is broken for
this trace.

A held noun phrase must also stay held semantically. If Layer A / compact `held` names
`full punishment doctrine`, `hiddenness`, `source-status`, or any other held item, Layer B
must not answer that item as topical commitment until a preceding state/noetic re-read
explicitly releases it with `Released: <item>`, `Released routes: <item>`, or
`Newly released routes: <item>`. Naming a held item as still held, withheld, or contrast
is permitted. Answering it without an explicit release marker is held-route semantic
leakage.

Failure conditions:

- Held item in Burden N-1 disappears from Burden N's Layer A without an explicit
  release event in Burden N-1's `Cleared` / `Newly released routes`.
- Held item named in Layer A or compact `held` appears in Layer B as an answered topical
  commitment before `Released: <item>` or an equivalent release marker appears in a
  preceding state/noetic re-read.
- Burden N's `Held routes` introduces material not anchored in the original input,
  prior held material, or the preceding collapse radius.
- A multi-burden response (≥ 2 burden-cycles) whose `Held routes` field is empty in
  every Layer A while the original input contained multiple input-anchored burdens.

## Failure Tests

- Failure condition: STOP is declared before state re-read names `next_eligible_pass: none`.
- Failure condition: a held route becomes eligible, but the response treats it as permanently
  suppressed.
- Failure condition: same-response RECURSE is refused solely because the user has not sent a new
  reply.
- Failure condition: default output prints `Recursion decision: RECURSE` or `next_eligible_pass:`
  as visible compliance instead of performing the prose transition and next bounded pass.
- Failure condition: "Move 1 / Move 2 / Move 3" headings replace state re-read and prose
  state transition.
- Failure condition: route legs are mislabeled as burden-cycles: FPD as Pass 1, M1 as Pass 2,
  DO-8 as Pass 3, M8 as Pass 4, or restoration as Pass 5 while Burden 1 has not landed.
- Failure condition: the current bounded operator is a route chain rather than one burden-level
  function.
- Failure condition: a TTP label is named in prose but the bounded operator is not actually
  selected, executed, and refreshed before downstream release.
- Failure condition: restoration synthesis or pastoral note appears before the active burden landing
  and state re-read.
- Failure condition: PARTIAL is collapsed into STOP when limits prevent an eligible next pass.
- Failure condition: multiple downstream arguments are dumped at one refresh instead of moving one
  live burden at a time.
- Failure condition: Component-Tour Surface-Compliance Failure ? the response covers all topics detected at initial
  read without state re-read between passes, without enumerating remaining input-anchored live
  burdens after each pass, and without routing one bounded live burden per burden-cycle. Covering all
  topics is not recursion. A response that covers all topics in one essay still fails recursion.
  input-anchored eligibility after refresh ≠ topic presence in the prompt.

Minimal pair: a governed same-response recursion follows a landed move plus refresh plus renewed
permission; an argument dump accumulates downstream content without refreshed governance.

- Failure condition: ungrounded noetic re-read ? a `Noetic re-read` block whose
  `burden landed` is asserted but the immediately preceding Layer B contains no operative
  submove with `target -> operation -> result` chain feeding the burden landing.
- Failure condition: noetic-equivalence prestige stack ? Ashʿarī, Māturīdī, Atharī,
  Taymiyyan, kalāmic, or falsafah-inflected sources cited as one unified operative
  authority for a school-sensitive claim.
- Failure condition: classical-theology umbrella ? `classical theology`,
  `classical theologies`, `classical Islamic theology`, `the classical tradition`,
  `mainstream kalām`, or `Ashʿarī/Māturīdī tradition` used as if it named one operative
  frame across contradictory schools.
- Failure condition: contrast-as-operative-support ? a source first marked `contrast`,
  `opponent-position`, `historical note`, `genealogy`, or `held material` is then used
  as operative warrant in the same burden-cycle without explicit reclassification.
- Failure condition: held-route semantic leakage ? Layer A names material as held, then
  Layer B answers that material as topical commitment before a preceding state/noetic
  re-read explicitly releases it.
- Failure condition: non-operative operation verb ? an `Operation:` line begins with
  generic prose such as `address`, `discuss`, `explore`, `engage`, or `consider` rather
  than one of the closed operative verbs.
- Failure condition: intra-school flattening ? a school is named as internally uniform
  (`Ashʿarī theology teaches X`, `Māturīdī theology teaches X`) on a claim that is
  internally disputed or school-sensitive without that qualification appearing.
- Failure condition: verbal-agreement smuggling ? agreement across frames is asserted
  without marking whether the agreement is substantive or only verbal/surface-level,
  and the asserted agreement is then used as operative support.
