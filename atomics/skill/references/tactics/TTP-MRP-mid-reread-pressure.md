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
  state before STOP, HOLD, RECURSE, PARTIAL, LoopBreak, or closure witness release.
- Field target: the post-landed reread field: current burden `ⁿB`, `ΔⁿB`, `Δκ`, held set `H`,
  dependency graph, terminal-state accounting, register deltas, target-explicit `∇·T` / `∇×T`,
  and `T_lang` boundary.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: freeze landed move -> activate matched pressure owners
  for dependency tug / hidden-framework recoil / entailment pressure / doubt-churn / reorientation
  -> aggregate their findings -> route result.
- Δ effect: `ΔⁿB` records what the landed move actually licensed; `Δκ` records whether activated
  pressure owners license graph movement, hold, recoil-bound status, LoopBreak, or no-edge closure.
- Possible ∇ reread: after pressure, check target-explicit `∇·B` for residual outward burden
  pressure and `∇×κ` for churn, circular reassurance demand, or label-pressure loop. The check is
  control-bound and target-explicit, not a truth/warrant metric.
- R(H,Δ) obligation: MRP runs inside `R(H,Δ)` before the final decision. It does not perform every
  pressure test itself; it activates the relevant existing TTP/operator owners and records what
  their outputs license for STOP, HOLD, RECURSE, PARTIAL, LoopBreak, graph delta, or closure.
- Hold/release/closure effect: stable pressure outputs permit closure witness; genuine dependency
  output requires RECURSE and a graph edge; partial real pressure output requires HOLD;
  hidden-framework recoil output is marked framework-concession-bound or equivalent and routed
  without pretending ordinary landing; doubt-churn / label-pressure / unlicensed recoil output
  requires LoopBreak or STOP; reorientation output holds proof-stacking and returns the field to
  already-landed signs / prior stable knowledge.
- Output boundary: `layer-b-permitted` only when MRP is invoked. Default output may render a compact
  `[Mid-Reread Pressure]` block only when it prevents false closure or infinite recursion; ordinary
  compact answers do not display the full block. `T_lang: Ψᴺ ⇢ Ψᴵ` remains partial coupling and does
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

MRP is not a brevity mechanism. It makes state reread operationally consequential: fake burdens
contract into STOP or LoopBreak, partial real burdens HOLD, genuine downstream burdens RECURSE with
graph evidence, and stable rereads release closure witness. It turns `R(H,Δ)` from a named refresh
into licensed burden economics: fewer fake burdens, more real burdens, and no unlicensed closure.

MRP also makes `∇·T` and `∇×T` active reread gates. `∇·T` asks whether post-landing burden
pressure dissipated or diverged into a genuine downstream burden. `∇×T` asks whether post-landing
pressure rotated back as churn, hidden-framework recoil, label-pressure, or self-reinforcing loop.
Neutral or settled `∇·T` plus null/resolved `∇×T` may license stable closure; non-neutral `∇·T`
requires HOLD/RECURSE explanation; non-null `∇×T` requires LoopBreak, STOP, HOLD, or graph-bound
recursion rather than decorative reporting.

MRP may license anticipatory downstream pressure: when a landed burden predictably exposes a
structurally licensed defense of the objection, MRP may activate matched TTPs to address that
defense before it is voiced. This must be graph-bound, commitment-bound, or framework-bound and
non-speculative; otherwise the route is STOP or closure, not pre-emptive expansion. MRP detects
and records the pre-emption gate; existing TTPs are the response machinery.

Each pressure activation slot must name one of three things: the matched TTP/operator used, the
pressure class used when the repo does not expose a narrower TTP ID, or an explicit TTP coverage
gap. MRP may not produce a finding from an unsupported slot. If a structurally necessary pressure
role has no current owner, record the coverage gap and route HOLD/PARTIAL or defer the pressure;
do not silently fold that missing work into MRP.

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
   - genuine new dependency -> RECURSE and attach graph edge;
   - partial but real burden -> HOLD;
   - churn / label-pressure / unlicensed recoil -> LoopBreak(∇×T) or STOP;
   - reorientation/reminder -> closure or HOLD without proof-stacking.

## Compact visible block

Use only when MRP is invoked and visible pressure prevents false closure:

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
Finding: stable | genuine-dependent | partial-real | hidden-framework-recoil | doubt-churn | reorientation
Graph delta: none | ⁿB → ⁿ⁺¹B
Pre-emption basis: none | graph-bound | commitment-bound | framework-bound
Route: STOP | HOLD | RECURSE | LoopBreak(∇×T)
Boundary: T_lang does not imply guaranteed uptake.
```

The compact block is not a replacement for the closure witness. If it creates or blocks graph
movement, the closure witness / `field_witness` evidence must agree.

## Field-witness hook

When `field_witness` is present, MRP evidence may be recorded as optional
`field_witness.reread_pressure`:

```json
{
  "target_burden_id": "B1",
  "reread_delta": "ΔⁿB landed; Δκ tested",
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
- Unsupported activation: a pressure slot produces a finding without naming an activated
  TTP/operator, named pressure class, or explicit TTP coverage gap.
- Recoil concession: hidden-framework recoil is marked but then treated as an unqualified landed
  burden.
- Infinite proof stack: doubt-churn is diagnosed but the response adds more proof instead of
  LoopBreak/STOP/HOLD.
- Uptake overclaim: MRP or `T_lang` claims acceptance, persuasion, conversion, guidance, or soul
  access.
