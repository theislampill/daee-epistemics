---
id: TTP-MRP-mid-reread-pressure
module_class: tactic
canonical_path: skill/references/tactics/TTP-MRP-mid-reread-pressure.md
contract_version: "0.4.0.0"
load_when:
  - Land(ⁿB) or partial Land(ⁿB) has been recorded
  - R(H,Δ) is deciding STOP / HOLD / RECURSE / PARTIAL / LoopBreak
  - a new burden appears during post-landed state reread
  - closure witness graph movement needs licensing
routing_effects:
  - activates matched pressure TTPs during R(H,Δ) before closure
  - records whether their outputs license graph delta, HOLD, RECURSE, LoopBreak, STOP, or closure
  - blocks false closure and proof-stacking when pressure owners expose unresolved state
companions:
  - recursive-state-transitions
  - diagnostic-ir
  - diagnostic-render-contract
  - output-release
  - P7-restoration-stops
output_shapes:
  - bounded-single-pass
  - recursive-traversal-permitted
layer_constraint: layer-b-permitted
catalogue_registered: true
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# TTP-MRP — Mid-Reread Pressure

## Runtime operator contract

- Activation: after `Land(ⁿB)` or partial `Land(ⁿB)`, while `R(H,Δ)` is rereading the landed
  state before STOP, HOLD, RECURSE, PARTIAL, LoopBreak, or closure witness release. MRP is the
  sound-reason pressure gate inside the reread: it asks which post-land pressure is now licensed
  before closure is released. In argumentative renders that pressure may correspond to a next
  escape route, but the formal owner is the field-state calculus, not imagined dialogue.
- Field target: the post-landed reread field: current burden `ⁿB`, `ΔⁿB`, `Δκ`, held set `H`,
  dependency graph, terminal-state accounting, register deltas, target-explicit `∇·T` / `∇×T`,
  and `T_lang` boundary.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: freeze landed move -> activate matched pressure owners
  for dependency tug / hidden-framework recoil / entailment pressure / doubt-churn / reorientation
  -> aggregate their findings -> route result.
- Δ effect: `ΔⁿB` records what the landed move actually licensed; `Δκ` records whether activated
  pressure owners license graph movement, hold, recoil-bound status, LoopBreak, or no-edge closure.
- Possible ∇ reread: after pressure, check target-explicit `∇·B` for residual outward burden
  pressure and `∇×κ` for churn, circular reassurance demand, or label-pressure loop; then read
  plain `∇` as the directional route-gradient over the refreshed field. The gradient asks where
  the field now pulls: toward an already-held burden, a generated resultant, HOLD/PARTIAL,
  LoopBreak, or STOP. The check is control-bound and target-explicit, not a truth/warrant metric.
- R(H,Δ) obligation: MRP runs inside `R(H,Δ)` before the final decision. It does not perform every
  pressure test itself; it activates the relevant existing TTP/operator owners and records what
  their outputs license for STOP, HOLD, RECURSE, PARTIAL, LoopBreak, graph delta, or closure.
- Hold/release/closure effect: stable pressure outputs permit closure witness; genuine dependency
  output requires RECURSE and a graph edge; partial real pressure output requires HOLD;
  hidden-framework recoil output is marked framework-concession-bound or equivalent and routed
  without pretending ordinary landing; doubt-churn / label-pressure / unlicensed recoil output
  requires LoopBreak or STOP; reorientation output holds proof-stacking and returns the field to
  already-landed signs / prior stable knowledge.
- Output boundary: `layer-b-permitted` only when MRP is invoked. Default routed output must render
  a compact `[Mid-Reread Pressure]` block for every burden-cycle route, because otherwise legacy
  `R(H,Δ)` can masquerade as pressure execution. Ordinary compact answers omit the block only when
  no burden-cycle route, HOLD/PARTIAL, LoopBreak, next burden, or closure is being released.
  `T_lang: Ψᴺ ⇢ Ψᴵ` remains partial coupling and does
  not imply guaranteed uptake.
- Negative constraints: no guaranteed uptake claim, no psychological acceptance claim, no proof-by-symbol,
  no truth/warrant overclaim, no scalar summary closure, no graph edge without terminal accounting,
  no RECURSE without a genuine dependency or explicit HOLD/PARTIAL reason, no proof-stacking after a
  LoopBreak condition, and no treating hidden-framework recoil as an unqualified landed burden.
- Fixture/checker: `tools/check_mid_reread_pressure.py` validates valid/invalid fixtures under
  `tests/mid-reread-pressure/`; `tools/check_ttp_operator_contracts.py --strict` validates this
  catalogue owner; closure graph / `field_witness` consistency is checked by
  `tools/check_closure_witness_graph.py` and `tools/check_ir_instance_integrity.py`.

## Formal owner contract

```json
{
  "schema": "formal-owner-contract-v1",
  "owner_id": "TTP-MRP-mid-reread-pressure",
  "owner_family": "MRP",
  "activation_feature": [
    "post-land R(H,Delta) reread",
    "target-explicit divergence/curl pressure",
    "held or generated route pressure before STOP"
  ],
  "field_target": [
    "current burden state DeltaB",
    "held set H",
    "B_LA/B_MRP membership",
    "dependency_graph",
    "terminal_states",
    "field_witness.formal_reread_states"
  ],
  "operation_token": [
    "mid-reread-pressure",
    "generated-burden-instantiation",
    "held-burden-activation",
    "no-new-resultant-proof",
    "hold-partial-route"
  ],
  "delta_result": [
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "hold_partial",
    "loopbreak"
  ],
  "reread_state_effect": [
    "records route_result_type before closure",
    "adds generated_by provenance when B_MRP is instantiated",
    "keeps coverage_complete=false while generated pressure remains unresolved"
  ],
  "hold_release_rule": [
    "STOP is licensed only when no live held/generated route remains",
    "generated unresolved pressure routes HOLD/PARTIAL/RECURSE with provenance",
    "catalogue presence alone is inert"
  ],
  "negative_examples": [
    "string-only generated_burden_instantiation marker without B_MRP parity",
    "route label used as owner ACT execution",
    "case-name or topic string used as MRP proof"
  ]
}
```

## Operation

MRP is the controlled activation harness inside `R(H,Δ)`. It does not answer a new topic and does
not replace the TTPs that perform hidden-framework, entailment, churn, or reminder work. It forces
the relevant pressure owners to operate in the reread interval and records what their outputs
license.

MRP is the post-Land escape-route discovery and preemption operator. Layer A owns the initial visible surface:
the current burden and any held burdens that are explicit, input-anchored, or necessary to keep a
compound from being flattened. Layer A should not dump every foreseeable downstream reply into the
initial inventory before any burden lands; doing so turns MRP into static dependency traversal and
weakens the sound-reason method. After `Land(ⁿB)`, `MRP(ⁿB)` freezes the landing, rereads
`ΔⁿB` / `Δκ`, tests `∇·B`, `∇×κ`, `ξ`, `Ω`, concealment, and held pressure, then asks: what
formal post-land pressure does the field now make eligible, and does that pressure require held
activation, generated burden instantiation, HOLD, LoopBreak, STOP, or closure? MRP is not
response-fanfiction or speculative reply generation; it converts licensed pressure into route
accounting, and only then, when the pressure is non-baseline, into a generated burden node.
MRP does not own the input burden dependency order; Layer A's graph/release structure does. MRP is
a lean detection/generation gate, not a content/refutation block. It names what just landed, what
escape route or pressure the reread detects, whether that pressure is already Layer-A-held or
genuinely new, and the resultant route. If the detected route is new, MRP instantiates a generated
burden using the next concrete ordinal token, such as
`⁶B [generated-by: MRP(⁵B)]`; the generated burden's own Layer B closes it with owner-bearing
submoves. The schematic form `ⁿ⁺¹B [generated-by: MRP(ⁿB)]` is theory grammar only and must not
be printed as a live public heading, MRP resultant, or closure-witness row. If the next burden was
already in Layer A / `H`, MRP records
`held_burden_activation`, but it did not generate the node.

Distinguish route result types:

- `held_burden_activation`: MRP authorizes movement to an already-inventoried held burden. The
  edge may be recorded as route provenance, but MRP did not generate the node.
  When the generating `formal_reread_states[]` row records `escape_routes_checked[]`, account the
  live held route with `"disposition": "held"` and the ASCII target such as
  `"target_burden": "B2"`. Do not write `held_burden_activation` in
  `escape_routes_checked[].disposition`; that underscore token belongs only in `MRP route result
  type` / `mrp_resultants[].type`.
- `generated_burden_instantiation`: MRP discovers a new resultant burden not fully present in the
  initial Layer A inventory. It must instantiate a normal burden node such as
  `⁶B [generated-by: MRP(⁵B)]` using the next concrete unused burden token.
  When the generating `formal_reread_states[]` row records `escape_routes_checked[]`, each live
  route object includes `type`, boolean `live`, `disposition`, `target_burden`, and `basis`.
  For the generated node, write `"live": true`, `"disposition": "generated-burden-instantiation"`,
  and the generated ASCII target such as `"target_burden": "B3"`. Do not write
  `generated_burden_instantiation` in `escape_routes_checked[].disposition`; that underscore token
  belongs only in `MRP route result type` / `mrp_resultants[].type`. Do not omit the boolean.
  This is an insertion into the governed route, not a replacement for the initial burden cycle:
  after the generated node lands or holds, return to any remaining input-anchored held burdens as
  `R(H,Δ)` and the route-gradient license them.
  The `Initial burden set` ledger is immutable: do not retroactively place generated nodes,
  HOLD/PARTIAL downstream nodes, or broader source-dossier nodes into it. List them separately in
  generated/partial/held accounting and terminal states.
- `no_new_resultant`: MRP finds no additional resultant burden; normal routing may continue to the
  next already-held burden or close if no eligible held burden remains.
  This is a no-edge proof, not a hypothetical next-token proof: do not name a
  future concrete burden token such as `⁴B` / `B4` to say it was not generated.
  Write `no newly generated burden`, `no new graph node`, or `no further B_MRP burden` instead.
  A terminal STOP/no-new row must carry `formal_reread_states[].no_new_resultant_proof`, not only
  a stable sentence. The proof object's `escape_routes_checked` is a list of eight objects with
  `type`, boolean `live`, and `basis`, using exactly these types: `closure-boundary-immunity`,
  `proof-carousel`, `total-system-exhaustion`, `doubt-churn`, `moral-tribunal`,
  `authority-order-recoil`, `hidden-framework-recoil`, and `restoration-recoil`.
  The `restoration-recoil` object also carries canonical `subtype` such as `scope-protest`.
  The proof records the field state at STOP (`divergence: neutral`, `curl: null|resolved`,
  literal string `b_live: "empty"`, `kappa_residual: 0`) and `stop_licensed: true`. If any route remains live,
  the row must account for it as generated, held, HOLD, PARTIAL, RECURSE, LoopBreak, or
  non-load-bearing; otherwise STOP is premature.
- `loopbreak`: MRP detects churn/curl and blocks proof-stacking.
- `hold_partial`: MRP detects real unresolved pressure and prevents false closure.

Worked counter-case: if Layer A declares `initial burden set: [¹B, ²B, ³B]` or a compact
`held: ²B, ³B` field, then `MRP(¹B)` routing to `²B` is `held_burden_activation`.
MRP may authorize the release edge, but it did not generate the node. Reserve
`generated_burden_instantiation` for a post-landing reread resultant not fully present in the
initial inventory and then instantiate that node with `[generated-by: MRP(ⁿB)]`.

General high-mass deployment rule: preserve the baseline Layer-A ledger while still testing for
extra post-Land escape routes. Write the baseline burden set as `𝔅_LA`: the burdens already
present in the input and worked by ordinary Layer-A release even without generated MRP. MRP may
add `𝔅_MRP`: generated burdens that surface only after `Land(ⁿB)` / `R(H,Δ)`. The total worked
ledger is therefore `𝔅_total = 𝔅_LA ∪ 𝔅_MRP`. In hard noetic, named-worldview, mixed-field,
source-worldview, source-authentication, authority-frame, moral-tribunal, proof-method,
identity/worldview-frame, historical/transmission, predication, or metaphysical cases, do not
count success as merely walking `𝔅_LA` by `held_burden_activation`. Also do not cripple `𝔅_LA` to
force a generated edge.
Instead, after each landing, test whether the renewed `ΔⁿB`, route-gradient `∇`,
divergence/curl state, ξ/Ω, and concealment pressure expose an additional non-baseline pressure
such as an immunity shield, authority-shift, proof-stack retreat, imported-model recoil,
source-order recoil, predicate recoil, formal-shell recoil, concealment pressure, or
shubhah/shakk-rāyb clarification pressure. If such a route is not already in `𝔅_LA` / `H`,
instantiate the next unused burden id as `ᵏB [generated-by: MRP(ⁿB)]`, work `ᵏB` with Layer B
owner-backed submoves, land it, then reread again and route back to any pending Layer-A-held burden
when licensed.
Do not print `ᵏB`, `ⁿB`, `Bn`, `Bk`, or `Bn -> Bn+1` as live public notation. They are grammar
slots in this tactic document; public/default output must instantiate them as concrete canonical
tokens such as `⁵B`, `⁶B`, `MRP(⁵B)`, `Land(⁶B)`, and `⁵B → ⁶B`.
Hybrid notation such as `ⁿB₁`, `ⁿB₂`, `ⁿB₃`, or `ⁿB₁₁` is also schematic, not live public
notation: it combines a generic burden superscript with a concrete subscript and breaks
reconstruction. Render the concrete burden/submove instead (`¹B`, `²B`, `¹B₁`, `²B₃`) in
headings, MRP targets, ACT records, terminal states, and Closure/Reconstruction Witness.
In public/manual smoke output, render the ledger with parser aliases alongside canonical notation:
`𝔅_LA (B_LA) = {...}`, `𝔅_MRP (B_MRP) = {...}`, and
`𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP`. These aliases are not a second formalism; they keep the
public witness and tools aligned while the canonical symbols remain primary. If a hard
generated-MRP smoke reaches STOP with `𝔅_MRP` empty, the smoke proves only held traversal, not
added-burden MRP deployment.
Do not print `B_total = B_LA + B_MRP` in the visible ledger. `+` describes only the final
`field_witness.B_total` array order (`B_LA` followed by `B_MRP`); visible proof uses `∪`.
Also reject visible ledger near-misses such as `B_total = B_LA union B_MRP`,
`B_total = B_LA ∪ B_MRP` without the canonical `𝔅_total (B_total)` field, or ASCII-only
`B_LA/B_MRP/B_total` burden economics when canonical glyph transport is available. The human
ledger must prove the union; the JSON payload proves ordered array membership.
Generated deployment also fails if it is achieved by under-inventory. For multi-anchor hard
noetic/source-worldview prompts, all explicit input-present burden anchors remain in
`𝔅_LA`: local wording/grammar, analogy, proof-text/source stack, authority-order appeal,
model/coherence claim, epistemic standard, moral tribunal, and named framework appeal. MRP may
release these nodes by `held_burden_activation`; it must not relabel them generated. If the output
prints `𝔅_LA = {¹B}` or `initial burden set: [B1]` while the prompt itself supplied multiple
support routes, the MRP proof is invalid even when `generated_burden_instantiation` appears.
The generated node must be additional post-Land pressure beyond the honest baseline ledger.
The ledger labels are non-droppable public witness fields. Print them in the first compact Layer A
header and in Closure/Reconstruction Witness; use paired ASCII aliases when transport cannot
preserve the canonical glyphs, never `?B`/`??B` substitutes. For hard noetic,
source-worldview, named-authority, or mixed-field manual smoke, a final non-neutral residual
framework/source-order/predicate pressure that is absent from `𝔅_LA` must either instantiate a
bounded generated `𝔅_MRP` burden with Layer B treatment or name a concrete owner/load boundary.
Do not hide that residual pressure behind `hold_partial` while still presenting the output as the
v0.4.3.0 generated-MRP proof.
Treat boundary-as-immunity recoil as a generic generated-candidate pressure: once the baseline
proof-text, authority-order, predicate, or source-status burdens have landed, a hard case may try
to convert the answer's boundedness into a shield ("the whole system was not exhausted, so the
local reply survives"). If that pressure was not already a baseline `𝔅_LA` burden, MRP instantiates
it as the next generated burden, then Layer B works the distinction between a bounded local
refutation and exhaustive system refutation. This prevents the closure boundary itself from
becoming an unworked escape route without naming any smoke-specific probe.
For that generated burden, "work" means operation-shaped TTP execution, not a conclusion-shaped
summary. The submoves must perform the owner/TTP appropriate to their bracketed operator, show why
that operation is live after the prior `Land(ⁿB)`, record the state delta, and explain how the
delta contributes to `Land(ᵏB)`. Hidden-premise exposure is required for FPD-style moves, but it is
not the universal shape: M8 traces consequences, M9 repairs predication/category structure,
source-status or authority-order repair sorts source authority and hidden support, P7 bounds scope
and stop/reopen conditions, and LoopBreak exits circularity. In a boundary-as-immunity recoil, this
normally means distinguishing local claim closure from total-system exhaustion, blocking
proof-stack immunity, preventing unworked held-route smuggling, naming what would be required to
reopen held material as a new burden, and stating why STOP is licensed only for the scoped claim. A
generated burden whose submoves merely say "bounded refutation need not exhaust everything" or
"held material remains held" has not discharged the Brandolini mass.
For boundary-as-immunity / broader-system recoil, require paragraph-level operation bodies. The
FPD submove must identify the exact hidden premise ("unargued wider doctrine can retroactively
repair failed local evidence"), explain why it is a new premise rather than a rescue of the landed
premise, and force it to be tested as its own burden. The scope/source-status submove must separate
"this offered reply failed" from "the entire system is exhausted", name the conditions under which
a new text or doctrine can become live, and prevent held material from acting as hidden support.
The P7/stop submove must describe the proof-carousel pattern, require a fixed interpretive
criterion before more prooftexts function as evidence, and state the STOP/HOLD boundary. If these
operations are replaced by short conclusion sentences, `Land(ᵏB)` is premature.
Therefore `hold_partial` is not the normal terminal result for this pattern. If the final reread
names broader taxonomy, proof-text rotation, full-system exegesis, framework immunity, or
boundary-as-immunity pressure with non-neutral `Field diagnostics: ∇·B ...` or non-null
`∇×κ ...` and `𝔅_MRP` is still empty, the route is not closure-ready. Generate and work the
bounded extra burden unless a concrete owner/load boundary prevents it; only that boundary may
justify PARTIAL.
For v0.4.3.0 manual/default proof, the final MRP pass MUST treat "broader material held" as a
candidate escape route, not as automatic closure. If broader-held material cannot rescue the local
reply, say so as `no_new_resultant`; if it can be used as an immunity shield, instantiate the next
generated burden and work it before STOP. A closure witness with `𝔅_MRP = {}` plus unresolved
framework-immunity language is evidence of baseline traversal only.

Before final STOP in a hard case, MRP inside `R(H,Δ)` must account for whether any post-Land
non-baseline pressure remains live after the baseline ledger lands. If the route-gradient,
`∇·T`/`∇·B`, `∇×T`/`∇×κ`, concealment pressure, or held-field reread exposes a distinct extra
pressure absent from `𝔅_LA`, instantiate it as `𝔅_MRP`, work it through Layer B, land it, and
reread again. If STOP is claimed instead, STOP must state why no such non-baseline route remains
live instead of merely saying the baseline ledger is exhausted.
For public generated-MRP proof, use canonical burden notation rather than ASCII parser aliases:
`¹B`, `²B`, `¹B → ²B`, `Land(¹B)`, and `R(H,Δ)`. A generated burden heading MUST carry the
generated provenance marker on the burden node itself:
`## Burden 2 / ²B [generated-by: MRP(¹B)] — <title>`. ASCII forms such as `B1`, `B2`,
`B1 -> B2`, `Land(B1)`, or `R(H,Delta)` are transport/checker fallbacks, not the default
public generated-burden proof surface; when transport forces ASCII, use
`## Burden 2 / B2 [generated-by: MRP(B1)] - <title>`.

MRP is not a brevity mechanism. It makes state reread operationally consequential: fake burdens
contract into STOP or LoopBreak, partial real burdens HOLD, genuine downstream burdens RECURSE with
graph evidence, and stable rereads release closure witness. It turns `R(H,Δ)` from a named refresh
into licensed burden economics: fewer fake burdens, more real burdens, and no unlicensed closure.

MRP also makes `∇`, `∇·T`, and `∇×T` active reread gates. `∇·T` asks whether post-landing burden
pressure dissipated or diverged into a genuine downstream burden. `∇×T` asks whether post-landing
pressure rotated back as churn, hidden-framework recoil, label-pressure, or self-reinforcing loop.
Plain `∇` asks where the refreshed field now points. Neutral or settled `∇·T`, null/resolved
`∇×T`, and no remaining route-gradient toward an input-anchored burden may license stable closure;
non-neutral `∇·T` or a route-gradient toward held/generated pressure requires HOLD/RECURSE
explanation; non-null `∇×T` requires LoopBreak, STOP, HOLD, or graph-bound recursion rather than
decorative reporting.
Directed downstream dependency is not curl. If `Bn -> Bn+1` is acyclic and linearly
traversable, residual pressure is recorded as non-neutral `∇·T` while `∇×T` stays null. Use
held/non-null/resolved curl only when a real circular dependency, churn, hidden-framework recoil,
label-pressure, dependency rotation, or loop was named; do not say curl resolved merely because a
linear chain was traversed.

Route consequence invariant: if the MRP record names a remaining live burden, proportionality
pressure, hiddenness/coercive-guidance pressure, source-worldview pressure, owner-floor pressure,
owner-body pressure, non-neutral `∇·T`, non-null/held `∇×T`, or a graph edge, the next public
move must release and land that burden, explicitly HOLD it with a named gate, or mark PARTIAL
with the blocked burden/owner. `STOP`/COMPLETE is invalid while the same record still names an
unresolved live pressure. If another burden or Layer B body follows, or the closure graph later
contains an edge out of the current burden, the current MRP record cannot be `stable`/`STOP`; it
must record the dependency as `genuine-dependent`, add the graph edge, and route `RECURSE` into
the next burden. Owner-load failure is not `Route: PARTIAL`; use `Route: HOLD` and put `PARTIAL /
OWNER-BODY-NOT-LOADED: <missing owner/path>` in `Boundary`.

For invocation purposes, `T` is the whole reread pressure field, not only the literal printed
token `T`. It includes `B`, `κ/H`, held dependencies, register pressure, and downstream burden
pressure. Visible `∇×κ`, `∇×B`, `∇×H`, remaining live burden, release-next, HOLD/PARTIAL,
LoopBreak, blocked proof-stacking, hidden-framework recoil, doubt-churn, or pre-voiced downstream
defense is therefore an MRP invocation point. The output must not jump from `Land(Bn)` to the next
burden or closure by legacy `R(H,Δ)` alone.

MRP may license anticipatory downstream pressure: when a landed burden predictably exposes a
structurally licensed defense of the objection, MRP may activate matched TTPs to address that
defense before it is voiced. This must be graph-bound, commitment-bound, or framework-bound and
non-speculative; otherwise the route is STOP or closure, not pre-emptive expansion. MRP detects
and records the pre-emption gate; existing TTPs are the response machinery. If the defense was
already fully identified in the initial burden inventory, classify the route as
`held_burden_activation`. If it surfaces only after `Land(ⁿB)` / `R(H,Δ)`, classify it as
`generated_burden_instantiation` and instantiate the new node with its own Layer A, Layer B,
owner-bearing submoves, Land/HOLD accounting, and closure-witness / `field_witness` record.
The generated case must say what legitimate post-land pressure / escape-route state became live,
why that route was not already in Layer A / `H`, what `ΔⁿB` revealed, and where the plain
route-gradient `∇` now points. In public dialectical prose this may be glossed as the serious next
retreat the argument now exposes, but the proof must remain the reread calculus:
`Land(ⁿB) -> ΔⁿB/Δκ -> ∇/∇·T/∇×T -> R(H,Δ) containing MRP -> resultant route`. If that explanation
is absent, MRP may STOP/HOLD/LoopBreak, but it may not claim `generated_burden_instantiation`.

Each pressure activation slot must name one of three things: the matched TTP/operator used, the
pressure class used when the repo does not expose a narrower TTP ID, or an explicit TTP coverage
gap. MRP may not produce a finding from an unsupported slot. If a structurally necessary pressure
role has no current owner, record the coverage gap and route HOLD/PARTIAL or defer the pressure;
do not silently fold that missing work into MRP.
Do not hardcode MRP to FPD/M1/M8. Those are examples. MRP may dispatch to any repo-native
operator whose owner is matched by the pressure, including FPD, M1, M1-P, M8, M9,
source-status repair, authority-order repair, criterion-reversal, definition-discipline, P1, P7,
doubt-vs-skepticism, regress-dissolution, and other catalogue owners. A generated burden that
always defaults to the same small TTP set regardless of pressure type is under-routed.

1. **Freeze the landed move.** Use existing burden/closure/terminal-state machinery to record what
   `Land(ⁿB)` actually licensed.
2. **Tug the dependency graph.** Use closure-witness graph / `field_witness` machinery to record
   whether `ⁿB → ⁿ⁺¹B` is licensed, including a pre-voiced recoil test when the nearest defense of
   the objection is structurally licensed by the current graph, commitments, or active framework.
3. **Activate hidden-framework recoil owners.** Use existing owners such as foreign-premise,
   definition, grief/register, loaded-label, source-status, or concession-boundary operators where
   live; MRP records whether the apparent burden is genuine or framework-concession-bound.
4. **Activate entailment pressure owners.** Use existing owners for internal-commitment pressure,
   consequence tracing, contradiction exposure, or premise review; MRP records whether the new
   burden collapses, splits, or exposes a deeper premise.
5. **Activate doubt-churn owners.** Use existing owners for wiswās-like churn, infinite
   reassurance demand, regress, or self-undermining doubt; MRP records whether
   `LoopBreak(∇×T)`, STOP, or HOLD is licensed.
6. **Activate reorientation/reminder owners.** Use existing owners for already-landed signs, prior
   stable knowledge, `fiṭrah`, `ʿaql ṣarīḥ`, or non-proof-stacking closure; MRP records whether
   closure, HOLD, or reminder/reorientation is licensed.
7. **Route from aggregated owner outputs.** Emit one governed result:
    - stable reread -> closure witness;
    - already-inventoried held dependency -> `held_burden_activation`, RECURSE/HOLD, and graph
      provenance;
    - newly surfaced resultant dependency -> `generated_burden_instantiation`, instantiate
      `ⁿ⁺¹B [generated-by: MRP(ⁿB)]`, RECURSE/HOLD, and attach graph edge;
    - no additional resultant -> `no_new_resultant` and ordinary route/closure discipline;
    - partial but real burden -> HOLD;
    - churn / label-pressure / unlicensed recoil -> LoopBreak(∇×T) or STOP;
    - reorientation/reminder -> closure or HOLD without proof-stacking.

## Compact visible block

Use in every default routed burden-cycle. In default hard/multi-burden output, this block is the
mandatory route gate between a concrete `Land(¹B)` / `Land(²B)` / current burden token and any Field diagnostics, LoopBreak, route-bearing
`R(H,Δ)`, next burden, HOLD/PARTIAL, or closure:

```text
[Mid-Reread Pressure]
Target: ¹B / <landed burden name>
R(H,Δ): held routes rechecked: <held baseline routes or none>; live remainder: <pressure or none>; release/next: <held/generated/STOP/HOLD/RECURSE/closure>
Landed delta: Δ¹B{...} / Δκ
Pressure activations:
- freeze-landed-move: <existing owner/TTP id or pressure class>
- dependency-tug: <existing owner/TTP id or pressure class>
- hidden-framework-recoil: <existing owner/TTP id or pressure class>
- entailment-pressure: <existing owner/TTP id or pressure class>
- doubt-churn-guard: <existing owner/TTP id or pressure class>
- reorientation-reminder: <existing owner/TTP id or pressure class>
Field diagnostics: ∇·B: neutral | non-neutral / <what this licenses>; ∇×κ: null | resolved | non-null / <what this licenses>
Route-gradient: <where ∇ now points; for held_burden_activation write "already-held ²B / B2 from Initial burden set / B_LA"; for generated write "newly generated ⁶B absent from B_LA after Δ⁵B">
Finding: stable | genuine-dependent | partial-real | hidden-framework-recoil | doubt-churn | reorientation
MRP route result type: held_burden_activation | generated_burden_instantiation | no_new_resultant | loopbreak | hold_partial
MRP resultant: <finding -> route/graph/HOLD consequence>
Graph delta: none | ¹B → ²B
Pre-emption basis: none | graph-bound | commitment-bound | framework-bound
Route: STOP | HOLD | RECURSE | LoopBreak(∇×T)
Boundary: T_lang does not imply guaranteed uptake.
```

The compact block is not a replacement for the closure witness. If it creates or blocks graph
movement, the closure witness / `field_witness` evidence must agree.
The block heading and fields are parseable. The heading is literal `[Mid-Reread Pressure]`; the
next line is a concrete target such as `Target: ¹B / <landed burden name>`; the next route-bearing line is `R(H,Δ): held routes rechecked: ...; live
remainder: ...; release/next: ...`. Do not write `R(H,Δ): [Mid-Reread Pressure]`, omit `Target:`,
or move `Field diagnostics:` outside the block. `Route:` is one exact value only: `STOP`, `HOLD`,
`RECURSE`, or `LoopBreak(∇×T)`. Do not append targets or prose to `Route:`; write `Route: RECURSE`
with the destination recorded in `R(H,Δ)`, `MRP resultant`, and `Graph delta`.
The target, generated-by source, route-gradient, MRP resultant, and graph delta must be concrete
public tokens. `Target: ⁿB`, `MRP(ⁿB)`, `Land(ᵏB)`, `Bk / ᵏB`, and `Graph delta: Bn -> Bn+1`
are schematic documentation forms, not valid public/manual output.
If `MRP route result type:` is `held_burden_activation` or `generated_burden_instantiation`, or if
`Graph delta:` adds an edge, use `Finding: genuine-dependent`. `Finding: stable` is terminal-only:
use it only with `MRP route result type: no_new_resultant`, `Graph delta: none`, and `Route: STOP`.
Hidden-framework recoil may be the pressure source, slot, or resultant explanation, but it is not the
graph-edge finding for held or generated burden movement.
Print literal `Route-gradient:` immediately before `Finding:`; do not let `Graph delta:` or
`Route:` carry the gradient silently.
For terminal `no_new_resultant`, the route-gradient may say no further burden remains, but it must
not print an unused future concrete burden token such as `⁴B` / `B4`; Grapher treats visible burden
tokens as nodes.
Default manual/public output must not render the legacy aliases `div.B`, `curl.k`, `curl.B`, or
`Reread: R(H,Delta)` as the primary surface. Use `∇·B` / `∇×κ` and literal `R(H,Δ):` with
`held routes rechecked`, `live remainder`, and `release/next` fields; pair ASCII aliases only
when an explicit glyph-transport fallback is needed.
Pressure activations must
render as six bullet slots, not one inline list. Each slot records the owner/TTP or pressure
class used and the release/hold/clear effect it licensed. A slot that merely names a pressure
without an effect is unsupported.
MRP must not contain submove-style refutation prose (`Operation:`, `Result:`, or
`Contribution-to-Land:`). That work belongs in the Layer B of the generated burden. A lean MRP block
with route/resultant/graph metadata is valid when it either releases a held Layer-A burden, records
STOP/HOLD/LoopBreak, or instantiates a generated burden that then receives full Layer B treatment.
`Route-gradient:` records the plain-`∇` direction after `Land(ⁿB)` and the pressure checks. In a
generated case, it must name the newly visible resultant and why the field now points there; in a
held activation case, it must show that the field points to a burden already in `H` / the initial
inventory. A block that has only `∇·T` and `∇×T` but no directional account is not enough to prove
preemptive MRP behavior.
For held activation, the gradient must name the held/initial burden token. For generated
instantiation, the gradient must name the newly generated pressure, its absence from `𝔅_LA`, and
the `ΔⁿB` / route-gradient change that made the new node live. Do not use generic arrow phrases
such as `grammar-pressure -> predication-pressure` as the whole gradient.
For `generated_burden_instantiation`, do not print the route type, graph edge, or generated node
until the block also includes literal `Route-gradient:` with the post-Land escape-route
explanation. MRP licenses the generated node; the generated node's own Layer B must then use
existing TTP/operator owners to answer it with Target/Operation/Result/Contribution-to-Land
submoves, a `Land(ⁿ⁺¹B)` statement, and post-land reread/MRP accounting unless terminal STOP is
explicitly licensed.
MRP must also identify the matched owner/TTP route for the pressure it preempts. It is not a
closed burden-name detector, not only FPD/M8/M9/P7, not a graph-edge generator, and not the
refutation itself. The formal route is:
`Land(ⁿB) -> ΔⁿB / Δκ -> ∇ / route-gradient -> ∇·T / ∇×T where licensed -> R(H,Δ) ->
MRP pressure read -> typed resultant -> matched owner/TTP route -> Layer B execution`.
If the pressure is already in `𝔅_LA`, `held_burden_activation` may release it, but the matched
owners still do the Layer B work. If the pressure is newly emergent, MRP records
`generated_burden_instantiation`, instantiates a concrete token such as
`⁶B [generated-by: MRP(⁵B)]` into `𝔅_MRP`, prints
`Matched owner/TTP route: [owners...]`, and routes the generated burden to those source-owned
operators. Layer B then activates those owners; code lookup is not owner activation. Owner examples
include V, M, E, F, R, P, source-status, authority-order, definition, transmission/testimony,
LoopBreak, restoration, and any other catalogue-owned owner whose operation matches the state-read.
MRP is never the owner code inside a Layer B submove bracket. Do not write `[MRP/P1]`,
`[MRP-source-status]`, or route-chain labels. Use the matched catalogue owner in the bracket and
record MRP provenance in the generated burden heading, MRP block, and field_witness.
When MRP leaves several owner/TTP candidates live for the same target burden, it must also emit a
deterministic owner activation plan: sequenced `required_before`, order-independent `parallel`
groups, `contingent` owners with trigger, `optional_non_load_bearing`, or `hold_partial`. This plan
governs the matched route, ACT record order, Layer B submove order, and
`field_witness.owner_activation_ordering`; optional or held owners are excluded from the canonical
required activation fingerprint. `required_before` entries are objects with `target`,
`before_owner`, and `after_owner`, not arrays of body refs or burden-event pairs.
The compact public activation record for the route is:
`⟦ACT ⁿBᵢ[OWNER.operation] :: π=<pressure-target> :: body_ref=ⁿBᵢ :: Δ=<ΔⁿB|Δκ>:<result> :: Land(ⁿB)+⟧`.
Use it after the matched owner/TTP route and before/inside the target burden's Layer B for every
baseline or generated burden that claims `Land(...)`, including the first baseline burden. It is
deliberately smaller than CALL/RET: it only says which owner operation is activated,
which pressure target it is working, which exact submove body proves it, which delta/result it
creates, and which Land it contributes to. `body_ref` must dereference to the exact submove block;
the record owner, matched route owner, and submove bracket owner must agree by catalogue-backed
family normalization. `π` must be visible in the body. `Δ` must be `ΔⁿB` or `Δκ` plus a concrete
result, and the dereferenced Result/Contribution text must show the burden-local state change and
Land contribution. A record without the body, a graph edge without owner operation, or package
presence without dereference proof is not MRP activation evidence. Do not add a second
model-authored `ACT_LEDGER`, `activation_record`, or verification-boolean surface as proof; the
checker canonicalizes activation facts from the ACT row, field_witness mirror, `body_ref`, and
dereferenced body, then fails disagreement.
There are no alternate ACT spellings: reject or rewrite `ΔACT`, bare unbracketed `ACT`, `Π=`,
`Τ=`, `Σ=`, `τ=`, `Λ=`, `Ξ=`, `pressure=`, `target=`, `delta=`, duplicate non-`Δ` field markers,
lowercase `δ=`, `DeltaB`, `DeltaK`, `Δ=∇B:...`, missing opening `⟦` or final `⟧`, and suffixes
such as `Land(...)+✓`, `Land(...)+R`, `Land(...)+MRP`, or `Land(...)+Δ`. ASCII burden ACT forms
such as `ACT B1_1[...]`, `body_ref=B1_1`, `Land(B1)+`, or `R(H,Delta)` are fallback/debug shapes,
not release-proof runtime output when Unicode transport is available. If the canonical ACT line
cannot be written from a real dereferenced owner body, route HOLD/PARTIAL instead of claiming
`Land(...)`.
The generated burden heading must be parseable:
`## Burden 6 / ⁶B [generated-by: MRP(⁵B)] — <title>` using the next concrete burden token. A bare
`Burden ᵏB — ...` heading leaves the generated burden inside the MRP block for parsers and is
therefore invalid for graphable output.
Generated-burden Layer A intake belongs inside that generated burden card, after the parseable
generated burden heading. Do not print `Layer A - Generated Burden Intake` as a free-standing
block before the generated node heading. Correct order:
`## Burden 6 / ⁶B [generated-by: MRP(⁵B)] — <title>` -> `#### Layer A - Generated Burden Intake`
-> `#### Layer B - Governed Operation Body`.
Owner activation has a visible body test. The selected owner must be recognizable in the generated
or held burden's operation body: M7 anchors definitions, M8 traces consequences, M9 repairs
predication/category structure, source-status/authority-order sorts source authority and hidden
support, P7 names scope/stop/reopen boundaries, and other catalogue owners perform their own
source-owned operation shape. Use `Result/state-change:` for high-mass submoves; that field and
`Contribution-to-Land(...)` must name a concrete state change, not merely restate the conclusion.
For M7/definition anchoring, `defined` or `stabilized` may be the concrete state change only when
the body actually anchors the contested term, relation, or criterion and shows what pressure that
definition removes.
For M8/consequence-trace, the state change is not merely `traced`; the trace must block, demote,
invalidate, expose-as-dependent, or hold-with-reason the pressure. For P1/restoration, the body
must name the restored criterion/order and any reopen boundary, not just provide warm closing prose.
Terminal STOP is not licensed when the MRP block itself says a doctrine-preserving,
source-worldview, framework, prooftext-harmonization, or other escape route is "identified",
"not released", "unreleased", or "held outside scope" while still live. In that case MRP must
generate the new burden when it was absent from Layer A, activate the held burden when it was
already inventoried, HOLD/PARTIAL it with a named gate, or LoopBreak it if it is churn/recoil.
`Held beyond prompt` is not a closure license by itself. This is selection-general across all
noetic-structure families: theology, secular moral protest, hiddenness, predication, canon/source
dispute, metaphysics, epistemology, identity/worldview-frame, moral tribunal, historical/
transmission, source-authority inversion, proof-stack/analogy-stack, and shubha/shakk/rayb cases.
When `R(H,Δ)` names any pertinent, high-leverage, TTP-addressable held route after `Land(ⁿB)`,
classify every named route before STOP: already in `𝔅_LA` -> `held_burden_activation` and release
it if current closure depends on it; absent from `𝔅_LA` and licensed by post-land pressure ->
`generated_burden_instantiation`; real but outside the bounded answer -> HOLD/PARTIAL with
`coverage_complete=false`; not actually live -> explain why it is non-load-bearing for this
prompt. Do not claim collapse/COMPLETE while load-bearing held routes remain unworked, ungenerated,
or unheld. A detected route cannot be ignored merely because it is large; large/high-mass routes
are where Brandolini pressure is highest.
When STOP is claimed after held routes were named, print visible classifications such as
`Held-route classification: <route> = non-load-bearing / <reason>` or
`<route> = HOLD/PARTIAL / <scope gate>`. A bare `held beyond prompt`, `held outside scope`, or
`none load-bearing` sentence is not enough; if the route is pertinent and not worked or proven
non-load-bearing, route HOLD/PARTIAL instead of COMPLETE.
Brandolini mass is diagnostic, not padding. Do not solve thin burden work with fixed submove
counts, generic length floors, or recap. Estimate burden mass from compression density, hidden
premise count, dependency radius / `κ`, proof-stack breadth, source/worldview load,
predication/category repair load, recoil probability, and closure risk. Bounded burden is not
light burden; local burden is not light burden; short surface phrase is not low mass. A concise
treatment is permitted only when the diagnostic state proves low mass: few hidden premises, low
dependency radius, no source-worldview load, no predication/category repair, no proof-stack or
textual backstop, no MRP-detected recoil, and low closure risk. Hard-compound noetic,
source-worldview, named-authority, or multi-burden inputs default to medium-high or high mass
unless the output proves otherwise. Before `Land(ⁿB)`, spend
enough owner-backed TTP mass to discharge the burden mass; otherwise route HOLD/PARTIAL rather
than landing tersely.
This mass gate applies to every Layer B burden that claims `Land(ⁿB)`. Baseline `𝔅_LA` burdens can
be high-mass when they carry proof-stack, source-order, predication/category, worldview, or hidden
premise pressure; generated `𝔅_MRP` burdens are especially suspect because they emerged from
post-land recoil, but they are not the only case. If Target/Operation/Result/Contribution fields
exist but merely restate the desired conclusion, the burden is not landed. Operation-shaped
submoves identify the exact premise/route, explain why it is operative in this input, apply the
owner action, produce a concrete state-change, and connect that change to `Land(ⁿB)`. If that
local operation cannot be rendered, route HOLD/PARTIAL rather than printing `Land(ⁿB)` and STOP.
Owner activation is owner-local. In hard/manual graphable proof, make the selected owner's
mechanism explicit in the operation body: FPD names the imported/foreign premise or criterion;
M1/M1-P names the self-grounding or speech-act contradiction; M3 identifies the orphaned
intuition and why it cannot stay severed from its ground; M7 anchors the definition or semantic
relation; M8 runs the consequence trace; M9 repairs predicate/category/referent/sense structure;
source-status/authority-order sorts sources, citations, proof texts, authority, and hidden support;
`do-christian-extensions` identifies the selected Christian pressure family and model/fan-out
route, and for selected DO-12 model pressure its ACT / `field_witness` operation is
`model-identification`, never bare `route`;
`do-second-loop` identifies the family-local hujjah/warning/record/accountability route;
`doubt-vs-skepticism` distinguishes normal doubt from skeptical methodology and names the
evidence-demand/modal-veto tribunal; P7 names STOP/HOLD/PARTIAL, held-route boundary, and reopen
condition; P1 restores positive orientation. Other catalogue owners follow their own source-owned
mechanism rather than a generic paragraph template.
For high-mass material, the compact fields should be followed by an operation body. For example,
an M8 consequence trace must do more than say a claim is vacuous: it should state the claim, trace
the exclusivity or consequence, test the proposed rescue, and show the state change. An M9
predication repair must do more than say sender and sent differ: it should identify the phrase,
separate predicate functions, test the transfer, and show why the analogy or proof-stack move
loses traction. MRP-generated burdens follow the same owner/TTP rule after MRP instantiates them;
MRP names the pressure, Layer B performs the operation.
Current hard/manual smoke proof should not end a medium/high-mass traversal with empty `𝔅_MRP`
when the last MRP block also relies on scoped closure, doubt-churn blocking, person-specific HOLD,
proof discipline, or public restoration to prevent recoil. Instantiate a generated
closure-boundary / immunity-recoil burden, route it to the matched owner family, work it in Layer B,
then reread. Empty `𝔅_MRP` is allowed only with explicit low-recoil proof in the MRP block and
`field_witness`.
For any selected hard-output proof, the boundary is stricter when closure names broader doctrine,
source-stack, proof-text stack, full-system metaphysics, proof-carousel, hidden-framework,
restoration-recoil, alternate exegesis, or bounded local reply language. Treat that boundary by
semantic state, not by case name: if it is live after Land, instantiate a concrete generated
`𝔅_MRP` burden such as `⁴B [generated-by: MRP(³B)]`, route it to P7/source-status/P1 or the
source-owned owners selected by the reread, execute its Layer B body, and only then STOP. If it is
not live, emit explicit `no_new_resultant_proof` evidence with checked escape routes, empty live
burden state, zero dependency residual, and `stop_licensed=true`. Do not close a selected
hard-output route with `𝔅_MRP = {}` merely by declaring the boundary non-load-bearing inside the
same final baseline burden.
The final non-load-bearing classification is itself a generated-boundary proof whenever broader
doctrine, source-stack, proof-text stack, full-system metaphysics, proof-carousel, hidden-framework,
or bounded-answer language appears in the final reread or closure and remains live. Even if the
initial ledger already contained a baseline boundary burden, post-Land boundary classification may
be a distinct MRP resultant. Instantiate and work the concrete `𝔅_MRP` burden when live, then
reread to STOP.
The closing tail cannot carry this proof by itself: Restorative Response, Closing Formulation, and
Closure/Reconstruction Witness may summarize the boundary only after a generated/held burden or an
explicit MRP HOLD/PARTIAL/non-load-bearing classification has already paid the recoil. Do not use
P7 warmth or a scoped closing sentence as a substitute for generated-recoil owner execution.
`Target:` must name the burden token explicitly, for example `Target: ²B / B2 state-enforcement
reduction`; mentioning `Land(²B)` only inside `Reread:` is not enough. If an older copied
template shows ASCII-first `Bn`, render it as `ⁿB / Bn / <landed burden name>` in live output.
In public `Landed delta`, `Route-gradient`, and pressure-activation prose, write `Land(²B)` or
`after ²B lands`, not ASCII-only `Land(B2)`. Reserve ASCII graph IDs for JSON fields and paired
fallback slots.

The compact block is a parseable record, not a prose paragraph. `Finding`, `Pre-emption basis`,
and `Route` must be one exact value from the template with no punctuation or added explanation.
It must include `MRP resultant: <finding -> route/graph/hold consequence>`.
For generated burdens, write the resultant in parseable public form:
`MRP resultant: genuine-dependent -> instantiate ᵏB [generated-by: MRP(ⁿB)]; route=RECURSE; matched owners=[...]`.
For held activation:
`MRP resultant: genuine-dependent -> release ᵏB from 𝔅_LA; route=RECURSE; matched owners=[...]`.
For STOP:
`MRP resultant: stable -> no_new_resultant; graph=none; route=STOP; held-route classifications=<...>`.
`MRP route result type` records whether the edge/routing is held-burden activation,
generated-burden instantiation, no new resultant, loopbreak, or hold-partial. Do not label normal
movement to an already-inventoried held burden as generated.
`Boundary` must begin `T_lang does not imply guaranteed uptake`; PARTIAL or owner-load boundaries
come after a semicolon. If no narrower owner/TTP id is exposed, begin the slot value with
`pressure class:`; if no owner exists, begin with `coverage gap:`. `Graph delta` is `none` unless
the route is `RECURSE`; held downstream route edges and generated node edges must be distinguished
by `MRP route result type`. The six pressure activation labels are fixed and must not be replaced by
generic pressure-class bullets. Each slot line must literally begin with `- <slot-name>:`; do
not omit the dash or colon. For doubt-churn / LoopBreak, `Graph delta:` is `none`; do not render
LoopBreak as a graph node or graph edge.
Each slot value must begin with an owner/TTP id, `pressure class: <name>`, or
`coverage gap: <missing owner>`. Do not begin a slot value with only a burden id, `none`,
`cleared`, or ordinary prose; inactive slots use `pressure class: none` or
`pressure class: cleared`.

MRP participates in reconstructibility/node-lineage accounting. A valid MRP pass must let the same node
lineage be reconstructed: input -> burden nodes -> submove nodes -> Land(Bn) -> R(H,Delta) ->
MRP resultant -> graph/field_witness delta or no-edge -> STOP/HOLD/RECURSE/LoopBreak/closure ->
restoration aim. If the MRP block cannot be mapped into that lineage, it is ornamental and cannot
license route or closure.

## Field-witness hook

Closure/Reconstruction Witness and `field_witness` are related but not identical. The Closure/
Reconstruction Witness is the human-readable proof ledger. `field_witness` is the
machine-readable graph/reconstruction payload used by checkers and Output Grapher. Normal
graphable output renders the tail in this order: Final Restorative Response, Closing
Formulation, Closure/Reconstruction Witness, then `field_witness`.

MRP evidence is encoded in `field_witness.reread_pressure` / MRP-resultant records when the
post-landed reread state is tested:

```json
{
  "target_burden_id": "B1",
  "reread_delta": "ΔⁿB landed; Δκ tested",
  "route_gradient": "∇ points to STOP; no held or generated burden remains in licensed scope",
  "pressure_activations": {
    "freeze_landed_move": "diagnostic-render-contract / terminal-state accounting",
    "dependency_tug": "closure witness graph machinery",
    "hidden_framework_recoil": "foreign-premise-detection or held pressure class",
    "entailment_pressure": "M8-reductio or M1-self-refutation",
    "doubt_churn_guard": "doubt-vs-skepticism or V3-regress-dissolution",
    "reorientation_reminder": "R2-the-reminder or P1-fitrah-restoration"
  },
  "divergence_state": "neutral",
  "curl_state": "null",
  "finding": "stable",
  "route_result_type": "no_new_resultant",
  "graph_delta": {
    "nodes_added": [],
    "edges_added": [],
    "note": "no new graph edge"
  },
  "preemption_basis": "none",
  "route": "STOP",
  "non_claims": ["T_lang does not imply guaranteed uptake"]
}
```

The sidecar is diagnostic and parser-stable. It does not replace Closure/Reconstruction Witness /
Restorative Response / Closing Formulation, and it does not upgrade local smoke evidence into
package-bound release proof unless the tested package surface actually produced or emitted the
sidecar. Closure/Reconstruction Witness and `field_witness` must agree on `B_LA`, `B_MRP`,
`B_total`, route graph, terminal states, MRP resultants, generated-by provenance, routes, closure,
`T_lang`, and non-claims. A mismatch means the output is not graphable/reconstructible.
For current graphable outputs, `field_witness` must use parser-stable JSON keys rather than only
free-form diagnostic objects. Include top-level `B_LA`, `B_MRP`, `B_total`, `nodes`, `edges`,
`generated_burdens`, `mrp_resultants`, `reread_records`, `field_diagnostics`,
`terminal_states`, `closure`, `T_lang`, `non_claims`, and `coverage_proof`. The
`coverage_proof` object includes `initial_burden_set`, `terminal_states`, and
`dependency_graph` with `nodes`, `edges`, `roots`, and `acyclic`. `mrp_resultants` records each
`MRP(Bn)` with source, type, route-gradient, graph delta, route, and generated/held/no-new route
effect so Output Grapher can validate without guessing from prose. The `route` value in each
`mrp_resultants[]` item copies the visible compact MRP `Route:` exactly, including
`LoopBreak(∇×T)` for curl/churn loopbreaks; do not replace it with transport aliases such as
`LoopBreak(del-cross(T))` in the machine payload.
Also include top-level `formal_reread_states[]`, one object for each visible `[Mid-Reread Pressure]`
block. This is a checker-readable mirror of the formal transition, not a trusted second proof
surface. Each object records `source_burden`, `prior_land`, `delta`, `reread`, `route_gradient`,
`divergence_state`, `curl_state`, `route_result_type`, `mrp_resultant`, `graph_delta`,
`preemption_basis`, and `route`. `divergence_state` is the first visible state token from the
block's target-explicit `∇·T` / `∇·B` diagnostic (`neutral`, `settled`, `bounded`, or
`non-neutral`); `curl_state` is the first visible state token from `∇×T` / `∇×κ` (`null`,
`resolved`, `held`, or `non-null`). When the
result type is `held_burden_activation` or `generated_burden_instantiation`, it also records
`next_burden` and `owner_route`; generated resultants also record `generated_by`. The checker
cross-checks these fields against the visible Land line, Landed delta, `R(H,Delta)`, Route-gradient,
target-explicit divergence/curl diagnostics, MRP resultant, graph delta, owner route, generated-by
provenance, Closure/Reconstruction Witness, and routed Layer B owner execution. If the visible block
and formal object disagree, the output is not reconstructible; if the visible block is missing, route
HOLD/PARTIAL rather than inventing a machine-only transition.
ACT records are mirrored in witness form without becoming a full CALL/RET grammar. The
Closure/Reconstruction Witness includes an `Owner activations:` ledger repeating the compact ACT
records for MRP-held or MRP-generated owner routes. Final `field_witness.owner_activations[]`
records `source`, `owner`, `operation`, `pressure`, `body_ref`, `delta`, `land`, and
`ordering_role` for the same activations. `parallel` and `optional_non_load_bearing` records include
`ordering_group`; `contingent` records include `trigger`. Output Grapher still reconstructs graph lineage from node/edge/resultant fields first;
the activation mirror is a semantic agreement layer that fails if the dereferenced body, route
owner, submove owner, delta, and Land contribution do not agree.
For an MRP-held or MRP-generated route, `source` is the MRP event that activated the route and
`target` is the burden worked by those ACT bodies. If `MRP(¹B)` releases already-held `²B`, every
`²Bᵢ` owner activation object uses `"source": "MRP(B1)", "target": "B2"`, not `"source": "B2"`.
If `MRP(³B)` generates `⁴B`, every `⁴Bᵢ` object uses `"source": "MRP(B3)", "target": "B4"`.
This source/target rule is how Closure/Reconstruction Witness, `field_witness`, and Output
Grapher reconstruct which reread licensed the owner route.
Inline `field_witness` uses a literal final heading and emits the parser-stable object itself; do
not hide it inside an unlabeled JSON block or a nested `{"field_witness": {...}}` wrapper.
Diagnostic status values must agree with the visible witness status heads and slash details:
`neutral / ...`, `non-neutral / ...`, `resolved / ...`, `null / ...`, etc. Do not use
field-witness-only wording such as `neutral after B6` when the readable witness says
`∇·B: neutral / ...`.

## Failure modes

- False closure: MRP says stable while terminal-state accounting or graph delta shows a genuine
  unresolved downstream burden.
- Decorative MRP: the block names MRP but does not freeze `ΔⁿB`, tug the graph, test recoil/churn,
  or route STOP/HOLD/RECURSE/LoopBreak.
- Cosmetic reread: `R(H,Δ)` is invoked but no observable reread consequence is recorded: closure
  stability, no-new-burden finding, graph edge, HOLD, recoil mark, LoopBreak, proof-stacking block,
  reorientation/reminder, closure witness update, or `field_witness` update.
- Decorative diagnostics: MRP claims closure while `∇·T` remains non-neutral without HOLD/RECURSE
  explanation, or while `∇×T` remains non-null without LoopBreak, STOP, HOLD, or graph-bound
  recursion.
- Dropped-live-burden: MRP names proportionality, hiddenness, source-worldview, moral-grounding,
  owner-floor, or owner-body pressure as live, but the output closes without releasing, landing,
  holding, or PARTIALing that pressure.
- Partial-closure leakage: `PARTIAL / OWNER-BODY-NOT-LOADED` appears, but the response continues
  into broad refutation, closure witness, Restorative Response, Closing Formulation, or "refuted"
  language for the blocked burden.
- Unsupported activation: a pressure slot produces a finding without naming an activated
  TTP/operator, named pressure class, or explicit TTP coverage gap.
- Generated-burden name theft: MRP calls an already-inventoried held burden "generated"; this
  steals Layer A's discovery job and blurs route provenance.
- Prose-only generated burden: MRP detects a new resultant but only mentions it in prose, without
  instantiating a normal burden node, Layer A/B accounting, owner-bearing submoves, Land/HOLD, and
  graph / `field_witness` evidence.
- TTP hardcoding: MRP-generated burdens always use FPD/M1/M8 despite a different pressure type,
  or fail to mark a coverage gap when no existing owner is available.
- Recoil concession: hidden-framework recoil is marked but then treated as an unqualified landed
  burden.
- Infinite proof stack: doubt-churn is diagnosed but the response adds more proof instead of
  LoopBreak/STOP/HOLD.
- Uptake overclaim: MRP or `T_lang` claims acceptance, persuasion, conversion, guidance, or soul
  access.
