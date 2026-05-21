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
  sound-reason preemption gate: it asks what the updated field now lets the interlocutor say next
  before closure is licensed.
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

## Operation

MRP is the controlled activation harness inside `R(H,Δ)`. It does not answer a new topic and does
not replace the TTPs that perform hidden-framework, entailment, churn, or reminder work. It forces
the relevant pressure owners to operate in the reread interval and records what their outputs
license.

MRP is the post-Land escape-route discovery operator. Layer A owns the initial visible surface:
the current burden and any held burdens that are explicit, input-anchored, or necessary to keep a
compound from being flattened. Layer A should not dump every foreseeable downstream reply into the
initial inventory before any burden lands; doing so turns MRP into static dependency traversal and
weakens the sound-reason method. After `Land(ⁿB)`, `MRP(ⁿB)` freezes the landing, rereads
`ΔⁿB` / `Δκ`, tests `∇·B`, `∇×κ`, `ξ`, `Ω`, concealment, and held pressure, then asks: what
would the interlocutor say next that this landing now reveals or enables?

Distinguish route result types:

- `held_burden_activation`: MRP authorizes movement to an already-inventoried held burden. The
  edge may be recorded as route provenance, but MRP did not generate the node.
- `generated_burden_instantiation`: MRP discovers a new resultant burden not fully present in the
  initial Layer A inventory. It must instantiate a normal burden node such as
  `ⁿ⁺¹B [generated-by: MRP(ⁿB)]`.
- `no_new_resultant`: MRP finds no additional resultant burden; normal routing may continue to the
  next already-held burden or close if no eligible held burden remains.
- `loopbreak`: MRP detects churn/curl and blocks proof-stacking.
- `hold_partial`: MRP detects real unresolved pressure and prevents false closure.

Worked counter-case: if Layer A declares `initial burden set: [¹B, ²B, ³B]` or a compact
`held: ²B, ³B` field, then `MRP(¹B)` routing to `²B` is `held_burden_activation`.
MRP may authorize the release edge, but it did not generate the node. Reserve
`generated_burden_instantiation` for a post-landing reread resultant not fully present in the
initial inventory and then instantiate that node with `[generated-by: MRP(ⁿB)]`.

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
mandatory route gate between `Land(Bn)` and any Field diagnostics, LoopBreak, route-bearing
`R(H,Δ)`, next burden, HOLD/PARTIAL, or closure:

```text
[Mid-Reread Pressure]
Target: ⁿB
Reread: R(H,Δ)
Landed delta: ΔⁿB{...} / Δκ
Pressure activations:
- freeze-landed-move: <existing owner/TTP id or pressure class>
- dependency-tug: <existing owner/TTP id or pressure class>
- hidden-framework-recoil: <existing owner/TTP id or pressure class>
- entailment-pressure: <existing owner/TTP id or pressure class>
- doubt-churn-guard: <existing owner/TTP id or pressure class>
- reorientation-reminder: <existing owner/TTP id or pressure class>
∇·T: neutral | settled | bounded | non-neutral / <what this licenses>
∇×T: null | resolved | held | non-null / <what this licenses>
Route-gradient: <where ∇ now points: held burden / generated burden / hold / loopbreak / stop>
Finding: stable | genuine-dependent | partial-real | hidden-framework-recoil | doubt-churn | reorientation
MRP route result type: held_burden_activation | generated_burden_instantiation | no_new_resultant | loopbreak | hold_partial
MRP resultant: <finding -> route/graph/HOLD consequence>
Graph delta: none | ⁿB → ⁿ⁺¹B
Pre-emption basis: none | graph-bound | commitment-bound | framework-bound
Route: STOP | HOLD | RECURSE | LoopBreak(∇×T)
Boundary: T_lang does not imply guaranteed uptake.
```

The compact block is not a replacement for the closure witness. If it creates or blocks graph
movement, the closure witness / `field_witness` evidence must agree. Pressure activations must
render as six bullet slots, not one inline list. Each slot records the owner/TTP or pressure
class used and the release/hold/clear effect it licensed. A slot that merely names a pressure
without an effect is unsupported.
`Route-gradient:` records the plain-`∇` direction after `Land(ⁿB)` and the pressure checks. In a
generated case, it must name the newly visible resultant and why the field now points there; in a
held activation case, it must show that the field points to a burden already in `H` / the initial
inventory. A block that has only `∇·T` and `∇×T` but no directional account is not enough to prove
preemptive MRP behavior.
`Target:` must name the burden token explicitly, for example `Target: B2 / state-enforcement
reduction`; mentioning `Land(B2)` only inside `Reread:` is not enough. If an older copied
template shows only superscript `ⁿB`, render it as `Bn / <landed burden name>` in live output.

The compact block is a parseable record, not a prose paragraph. `Finding`, `Pre-emption basis`,
and `Route` must be one exact value from the template with no punctuation or added explanation.
It must include `MRP resultant: <finding -> route/graph/hold consequence>`.
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

When `field_witness` is present, MRP evidence may be recorded as optional
`field_witness.reread_pressure`:

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

The sidecar is optional and diagnostic. It does not make ordinary compact output expose JSON, and
it does not upgrade local smoke evidence into package-bound release proof.

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
