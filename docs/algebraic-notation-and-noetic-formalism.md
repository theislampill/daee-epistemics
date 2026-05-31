---
title: Algebraic Notation and Noetic Formalism
status: theory-specification
contract_version: "0.4.0.0"
source_of_truth: false
canonical_runtime_owner: atomics/skill/references/diagnostics/diagnostic-ir.md
---

# Algebraic Notation and Noetic Formalism

This theory/specification surface preserves the algebraic formalism recovered from
`docs/index.html` and states what is now canonical. The schema-light register bridge is implemented in this repo as
baseline register formalism with register-derived control over the compact runtime. In the narrow
schema-boundary sense, it remains a derived/conditional bridge: atomics and generated runtime
define the bridge, and `tests/register-formalism-bridge-fixtures/` plus `tools/check_register_formalism_bridge.py`
prove the register terms map to existing owner, hold/release, burden-selection, reread, PARTIAL,
terminal, Shannon-boundary, and anti-symbol-theater controls. Schema-light means baseline
control without mandatory register fields; it does not mean optional theory, future parity, or
permission to ignore live registers. This is not a hard Diagnostic IR schema migration, a fresh
live-smoke claim, or a package/release proof claim by itself.

Current compact runtime spine:

```text
Input -> IR(N,m,tau,sigma) -> ∇ route-gradient -> ⁿB -> {ⁿBᵢ[OPᵢ]} -> Land(ⁿB) -> ΔⁿB/Δκ -> ∇·/∇× field diagnostics -> LoopBreak(∇×T) if licensed -> R(H,Δ) -> 𝒞(Ψᴺ) -> STOP/HOLD/PARTIAL/RECURSE
```

schema-light register bridge baseline:

```text
𝓝 ⊢ D₀ ⇝ Ψᴺ<N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H>
→ IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
→ ∇ route-gradient over eligible live pressure
→ [ⁿB → {ⁿBᵢ[OPᵢ]} → Land(ⁿB) → ΔⁿB/Δκ → ∇·/∇× target field state → LoopBreak(∇×T) when licensed → R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)]*
→ 𝒞(Ψᴺ) → N_fiṭrī ∧ ʿaql ṣarīḥ / ⁿ⁺¹B
→ T_lang: Ψᴺ ⇢ Ψᴵ
```

ASCII fallback:

```text
N_space |- D0 ~> PsiN<N in N_space,m,tau,sigma,heart,xi,Omega,mu,kappa,H>
-> IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)
-> route-gradient over eligible live pressure
-> [nB -> {nBi[OPi]} -> Land(nB) -> Delta-nB/Delta-kappa -> del-dot/del-cross target field state -> LoopBreak(del-cross(T)) when licensed -> R(H,Delta-nB{heart,xi,Omega,sigma,mu},Delta-kappa)]*
-> C(PsiN) -> N_fitri and aql_sarih / n-plus-1B
-> T_lang: PsiN -> PsiI
```

## Operator Typing / Schema-Light Formal Types

These are schema-light formal types. They clarify the mathematical role, valid use, and misuse
boundary of the notation without turning the repo into a full formal calculus. They also do not
make vector-calculus notation literal physical differential operators, and they do not prove
truth, warrant, interlocutor uptake, model-internal mechanism, or live behavioral competence.

| Operator | Schema-light formal type | Misuse boundary |
|---|---|---|
| `ΔⁿB` | Partial local state-update on burden-local and register-local state. | Not a decorative topic shift and not interchangeable with `ⁿ⁺¹B`. |
| `Δκ` | Dependency/collapse-radius graph update. | Not a generic TODO list or a proof that all dependencies were reread. |
| `∇` | Route-ranking functional from state and eligible route set to a preorder/scored ordering. | Not literal physical gradient, truth metric, warrant proof, or gate bypass. |
| `∇·T` | Post-`Δ` diagnostic predicate/label over explicit target subfield `T`. | Not literal divergence unless a rigorous target space is later defined. |
| `∇×T` | Cycle/circularity diagnostic over a relation/graph-like target `T`. | Not literal curl unless a rigorous target space is later defined. |
| `LoopBreak(∇×T)` | Owner-licensed partial transition, `⇀`, not total `→`. | Undefined unless cyclic pressure is diagnosed and a non-circular owner ground licenses repair. |
| `R(H,Δ)` | Reread transition over held material `H` and updated state. | Not satisfied by printing the marker without held/live remainder and next-status work. |
| `𝒞(Ψᴺ)` | Closure predicate on agent/runtime execution state. | Not interlocutor acceptance, conversion, persuasion, guidance, or soul access. |
| `T_lang: Ψᴺ ⇢ Ψᴵ` | Partial coupling relation at the public-output boundary. | Not an isomorphism, not a surjection, and not a guaranteed update operator on `Ψᴵ`. |

## Mid-Reread Pressure Reconstructibility

v0.4.3.0 adds Mid-Reread Pressure (MRP) to the operational chain as a reconstructibility
requirement, not as a decorative block. After `Land(Bn)`, `R(H,Delta)` must be able to recover
the MRP pressure resultant that licensed the next route: graph movement, HOLD, RECURSE,
LoopBreak, STOP, or closure. The release proof lineage is:

```text
input -> burden nodes -> submove nodes -> Land(Bn) -> R(H,Delta)
-> MRP pressure activations -> MRP resultant -> graph/route
-> next burden or closure -> restoration aim
```

Execution mass is not proof by itself, but hard-compound reconstructibility has visible output
cost. A hard-compound answer that claims complete traversal while hiding the burden/submove/MRP
lineage is under-executed even if it prints the right labels; a long answer without topology is
bloat.

## Small-Step Transition Model

This is the preferred mathematical home for the current notation: typed transition systems,
graph-state updates, and operational semantics. Vector-calculus language remains analogy unless a
rigorous target space is defined. In particular, `∇·` and `∇×` are target-explicit diagnostics,
not literal differential operators.

```text
S = (N_space, N_sel_or_held, B_live, H, κ, Reg, Routes, SourceBasis, Gate, RenderGate)

select:   Sᵢ ──∇──▶ (route preorder, chosen burden/operator)
operate:  Sᵢ ──ⁿBᵢ[OP]──▶ Sᵢ'
delta:    ΔⁿB, Δκ extracted from Sᵢ → Sᵢ'
diagnose: Sᵢ' ──(∇·T, ∇×T)──▶ diagnostic labels over explicit target T
repair:   if licensed, LoopBreak(∇×T): Sᵢ' ⇀ Sᵢ''
reread:   Sᵢ'' ──R(H,Δ)──▶ decision ∈ {STOP, HOLD, PARTIAL, RECURSE, ⁿ⁺¹B}
close:    𝒞(Ψᴺ) is a predicate on Sᵢ'' plus reread state
release:  T_lang: Ψᴺ ⇢ Ψᴵ is a partial coupling relation at the public-output boundary
```

`LoopBreak` is partial because it is licensed only under diagnosed cyclic pressure. `T_lang` is
partial because public language may fail to couple, be misunderstood, or be refused. `∇` ranks
eligible route pressure before release; it does not choose from the whole possible field after
routing gates have already excluded a path.

### Canonical Route Tiebreaker

`∇` may produce a preorder when multiple eligible routes are semantically parallel. For governed
output and reproducibility, the dispatch surface extends that preorder to a deterministic total
order before owner-plan emission:

```text
1. Source, criterion, and authority gates precede content owners.
2. Register weight breaks content-owner ties: Ω > ξ > μ > κ > heart.
3. Within the same register weight, catalogue position order wins.
4. Within the same catalogue position, lexicographic owner_id order wins.
```

Parallel routes may still be recorded as parallel when they are genuinely non-order-bearing, but
that parallelism must itself be explicit in `owner_activation_ordering.parallel_groups[]`.
Otherwise each load-bearing activation receives a `required_before` relation or falls under the
canonical total-order policy. This policy is a reproducibility discipline; it does not make owner
precedence a truth metric, and it does not override source/IR gates.

Science-only/source-totalization is the current narrow A.12 canary for this rule. When an input
claims that scientific explanation, empirical method, or scientific authority is the only
knowledge source or criterion, the source-order gate is live before the self-grounding test:
`source-status-repair.source-order` precedes `M1.self-grounding-test` on the same burden unless
the source-order pressure is explicitly proven non-load-bearing. The stable N-frame token for this
frame is `science-only-source-order-warrant`. Its exact pressure labels are
`scientific-explanations-only-knowledge-source` and `only-science-counts-standard`; its
machine-facing terminal-state maps use `{"B1": "landed"}`.

### Canonical Delta Result Token Discipline

`Delta-nB` and `Delta-kappa` records must preserve the local result token that names what changed.
For reproducibility, compact spellings such as `Delta(B1):predicate-separated`,
`Delta B1:predicate-separated`, and `Delta¹B:predicate-separated` normalize to the same structural
record:

```text
target = B1
delta_result = predicate-separated
```

The token after the target is load-bearing. It must not be discarded during activation
fingerprinting, NLA comparison, or witness reconstruction. Prose variation in the body may remain
free, but the structural `delta_result` slot is part of the activation state.

The bounded owner vocabulary for governed output is source-owned in
`atomics/skill/references/diagnostics/delta-result-vocabulary.json`
(`diagnostic-ir-delta-result-vocabulary-v1`) and copied into the compiled
runtime metadata as `references/diagnostics/delta-result-vocabulary.json`.
The table below mirrors that machine-readable source:

| Owner | Valid `delta_result` tokens |
|---|---|
| `M1` | `self-authorizing-standard-invalidated`, `internal-contradiction-exposed`, `criterion-self-failed`, `self-authorizing-falsifiability-standard-invalidated` |
| `M1-P` | `performative-contradiction-exposed`, `speech-act-presupposition-named` |
| `M3` | `orphaned-intuition-identified`, `grounding-severed`, `normativity-restored-to-ground` |
| `M7` | `definition-anchored`, `semantic-anchor-stabilized`, `term-meaning-bounded`, `falsifiability-standard-defined` |
| `M8` | `consequence-traced`, `implication-demoted`, `mechanism-totality-demoted`, `entailment-blocked`, `dependency-exposed`, `coercive-clarity-entailment-demoted`, `finite-answer-evasion-claim-invalidated`, `total-veto-consequence-demoted` |
| `M9` | `predicate-separated`, `category-separated`, `referent-separated`, `person-nature-transfer-blocked`, `sense-separated` |
| `FPD` | `hidden-tribunal-blocked`, `imported-criterion-blocked`, `foreign-premise-exposed`, `smuggled-support-blocked`, `imported-control-criterion-blocked` |
| `source-status-repair` / `authority-order-repair` | `source-order-repaired`, `hidden-support-blocked`, `science-source-bounded`, `proof-text-sorted`, `authority-order-repaired`, `proof-text-hidden-support-blocked`, `authority-order-separated`, `hidden-authority-source-status-bounded` |
| `P1` | `fitrah-reorientation-restored`, `tawhid-orientation-restored`, `sound-worship-frame-returned`, `fitrah-orientation-restored` |
| `P3` | `reason-revelation-order-stabilized` |
| `P7` | `scope-boundary-named`, `stop-condition-defined`, `held-route-bounded`, `reopen-condition-stated`, `personal-hiddenness-held-with-reason`, `reopen-boundary-licensed`, `shubhah-boundary-routed` |
| `LoopBreak` | `circular-dependency-broken`, `loop-grounded-in-owner-source` |
| `do-christian-extensions` | `trinitarian-model-identified`, `fan-out-route-named` |
| `doubt-vs-skepticism` | `doubt-distinguished-from-skeptical-methodology`, `burden-inverted`, `evidence-demand-tribunal-exposed`, `doubt-method-separated-from-sincere-question` |

The current v0.4.3.0 checker slice preserves and compares compact delta suffixes so drift cannot
hide behind equivalent `Delta(B)` targets, and rejects owner-local `delta_result` tokens outside
the source-owned vocabulary for the strict owner families it checks. The vocabulary includes both
the core formal tokens and the retained governed-smoke source-owned tokens needed to keep current
proof artifacts under the same hard gate. Diagnostic IR field-witness sidecars also use this source
for `normalized_activation_record.per_burden[].delta_result` validation.

### NLA Isomorphism Between Execution Traces

Two governed execution traces over the same normalized input `D0` are NLA-isomorphic when their
visible verbalization encodes the same structural execution state, even if their explanatory prose
varies. The isomorphism is over the noetic language activation slots, not over natural-language
surface identity:

```text
NLA_isomorphic(E1,E2) =
  same input_fingerprint
  and same selected or held N frame
  and same live register set {heart, xi, Omega, mu, kappa}
  and same InitialBurdenSet structure
  and same burden-to-register assignments
  and same owner_activation_ordering plan
  and for every B in B_total:
      same owner_id for each load-bearing submove
      same operation family
      same Delta target
      same delta_result token
      same MRP route result type
      same terminal state
      same generation_depth where generated
```

Allowed variation:

- explanatory prose inside the TTP Operation Body;
- sentence ordering inside a non-load-bearing paragraph;
- spelling variants that normalize to the same owner, target, token, or terminal state;
- explicitly declared parallel owner groups when the activation plan says the order is not
  load-bearing.

Disallowed variation:

- a different selected `N` frame or live-register set;
- a different register-derived burden floor;
- owner selection drift;
- owner ordering drift outside declared parallel groups;
- `delta_result` drift;
- MRP resultant-type drift;
- terminal-state drift;
- generated-depth drift.

This definition is the contract that `normalized_activation_record` will make machine-readable.
Until that schema field exists, reproducibility checks compare the currently available
field-witness owner plan, activation fingerprints, topology, pressure labels, and terminal states.

### Normalized Activation Record Field

`field_witness.normalized_activation_record` is the schema-light carrier for the NLA isomorphism
slots. It strips explanatory prose and keeps the structural state needed for repeated-run
comparison:

```json
{
  "n_frame": "selected-or-held-frame",
  "live_registers": ["xi", "Omega", "mu", "kappa"],
  "burden_floor": ["B1", "B2"],
  "per_burden": [
    {
      "burden_id": "B1",
      "owner_id": "M9",
      "operation": "predication-repair",
      "delta_result": "predicate-separated",
      "mrp_route_result_type": "generated_burden_instantiation",
      "terminal_state": "landed",
      "generation_depth": 0
    }
  ]
}
```

`burden_floor` is a string list of B IDs. `per_burden[]` keeps its historical
field name, but the rows are owner-activation/submove level: a burden with three
load-bearing owners emits three rows with the same `burden_id` and distinct
`owner_id` / `operation` / `delta_result` tuples.

`n_frame` is a stable Diagnostic IR frame token, not explanatory prose. Repeated runs over the
same frame reuse the same kebab-case token, including the science-only canary token
`science-only-source-order-warrant`.

`delta_result` in this record is the suffix token only. It records
`science-source-bounded`, not `Delta(B1):science-source-bounded`; the burden-local target lives in
the ACT/owner activation delta field.

The record is not a self-authenticating proof. The convergence checker validates it against
source-owned witness fields: `B_LA`, `B_total`, live-register obligations, `owner_activations`,
`mrp_resultants`, terminal states, and generated-burden depth. If it disagrees with those fields,
the normalized record fails rather than rewriting the proof around itself.

### Termination Proof For The MRP Generation Chain

For the state

```text
S = (N_space, N_sel_or_held, B_live, H, κ, Reg, Routes, SourceBasis, Gate, RenderGate)
```

the eligible route set `R(S)` is finite at every step: it is bounded by the finite owner
catalogue, the finite current burden/register set, and the IR/routing/owner gates that constrain
`∇`. The `select` step therefore chooses from a finite preorder rather than from an unbounded
search space.

Every `operate` step `ⁿBᵢ[OP] -> Sᵢ'` has one of two effects. Either it lands, discharges, or
honestly holds the current burden, reducing the unresolved part of `B_live`; or it generates a
new burden through `Land(B)+R(H,Delta)`. Generated burdens are ordered by the depth function:
baseline burdens in `B_LA` have depth `0`, and a generated child `B'` has
`d(B') = d(B)+1` relative to its parent. The field witness records this as
`generated_burdens[].generation_depth` and `coverage_proof.max_generation_depth`. Since the
checked traversal has a finite maximum depth and generated children must be strictly deeper than
their parents, the generation graph is well-founded for the witnessed execution.

`LoopBreak(∇×T)` is a partial transition (`⇀`), not a total step. It can fire only when nonzero
curl is diagnosed and a licensed ground from the closed LoopBreak vocabulary is present. A valid
LoopBreak names the target, ground, delta, and post-break reread; it therefore resolves or bounds
the circular dependency that triggered it instead of adding another unbounded proof request.

Thus every witnessed execution sequence reaches one of the finite terminal modes:

```text
STOP | HOLD | PARTIAL | RECURSE-to-a-strictly-deeper/generated-or-inventoried-burden
```

This is a machine-auditable termination discipline for the witnessed graph, not a theorem about
all possible future interlocutor replies or a claim that no later burden can be posed.

## Closure Coverage And Collapse Proof

The Closure/Reconstruction Witness uses the burden dependency graph as both a dependency
structure and a coverage record. `A → B` means B depends on A landing first; `A ∥ B` means the
two burdens are parallel in the current witness; `(root)` means no upstream dependency. Dropping
an initial burden from terminal accounting is a proof failure, even if the response prints
`R(H,Δ)`.

The visible graph is the human-readable reconstructibility layer. When a development, smoke, or
audit artifact needs machine-readable reconstruction, a `field_witness` sidecar carries the same
burden nodes, dependency edges, roots, parallel groups, terminal states, register deltas, `∇·` /
`∇×` diagnostics, LoopBreak data, `R(H,Δ)`, closure status, `T_lang` boundary, non-claims, and
provenance/evidence metadata. The two layers must agree; neither layer upgrades local diagnostic
evidence into package-bound release proof.

`InitialBurdenSet` is not a retrospective set inferred from the closure block. It is the
pre-release burden enumeration supplied by Layer A / Diagnostic IR before terminal accounting.
New burdens found during `R(H,Δ)` are newly live or next-pass candidates; they do not make the
original initial set larger after the fact.

Initial burden completeness is checked against the live register set, not against the model's
retrospective claim that the listed burdens were enough:

```text
diagnostic_complete(D0, IR, B_LA) =
  for every r in live_registers(IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)):
    some B in B_LA has register_type(B) covering r
```

The machine witness records this as `coverage_proof.diagnostic_completeness`, including the live
register list and a register-to-burden coverage mapping. A complete coverage certificate therefore
has two directions: soundness, where every claimed burden is valid and terminally accounted, and
diagnostic completeness, where the structural live-register obligations were not silently omitted
from `B_LA`.

Generation depth is the well-founded ordering over generated burdens:

```text
d(B) = 0         for every B in B_LA
d(B') = d(B)+1   when B' in B_MRP is generated by Land(B) + R(H,Delta)
```

Every `field_witness.generated_burdens[]` entry for a `B_MRP` node carries
`generation_depth`; `coverage_proof.max_generation_depth` records the finite maximum over the
whole burden graph, with baseline-only traversals recording `0`. A generated child must have
depth strictly greater than the parent named in `generated_by: MRP(B)`. This makes the
termination argument auditable as a finite graph discipline rather than a prose assertion that
generated burdens are exhausted.

```text
coverage_complete =
  every burden in InitialBurdenSet appears exactly once in TerminalStates

collapse_positive =
  coverage_complete
  and ∇·B = neutral
  and ∇×κ ∈ {null, resolved}
```

Held or carried burdens can be valid terminal states for current-pass accounting:
`held-with-reason`, `carried-PARTIAL`, and `carried-RECURSE` prevent silent drops. They must not be
mistaken for COMPLETE closure unless the witness also explains why the scoped field has no live
outward pressure and no unresolved curl. Coverage completion is an accounting condition; positive
collapse is a stronger closure condition.

### MRP Exhaustion Lemma

Define `B_live` after traversal as the set of burdens in `B_total` whose terminal state is absent
or whose state is live without a HOLD, PARTIAL, or RECURSE disposition. Define `∇·B` as the
post-Delta diagnostic predicate over that burden field. If `B_live` is non-empty after traversal,
there remains outward burden-field pressure, so `∇·B` is non-neutral. Therefore, by
contraposition:

```text
∇·B = neutral  ->  B_live = empty
B_live = empty ->  every B in B_total is terminally accounted
```

Since `B_MRP` is a subset of `B_total`, neutral burden divergence implies every generated MRP
burden is either landed, discharged, held with a reason, or explicitly carried as PARTIAL/RECURSE.
It does not mean that the interlocutor accepted the response, that no later question can arise, or
that a literal vector-divergence theorem has been proven. It means the runtime's current burden
graph has no silent generated burden left outside terminal accounting.

### Typed Escape Routes

`escape_routes(D0, traversal)` is the finite typed set of post-Land routes that could preserve
the defeated claim if the runtime silently skipped them. The closed v0.4.3.0 type set is:

```text
escape_routes = {
  closure-boundary-immunity,
  proof-carousel,
  total-system-exhaustion,
  doubt-churn,
  moral-tribunal,
  authority-order-recoil,
  hidden-framework-recoil,
  restoration-recoil
}
```

After `Land(Bk) -> R(H,Delta)`, each live escape-route type must be accounted by one of these
typed dispositions:

```text
generated_burden        -- instantiate a generated B_MRP node and route RECURSE
held / PARTIAL / RECURSE -- carry the pressure honestly with a reason
LoopBreak               -- when the route is a licensed curl/cycle repair
non-load-bearing        -- explicitly prove the route is not live in this traversal
```

The field witness may record this as `formal_reread_states[].escape_routes_checked[]`, where each
entry names the escape-route `type`, whether it is `live`, the typed disposition when live, the
target/generated burden when applicable, and a non-empty `basis`. This is a closure discipline:
printing `STOP` or `no_new_resultant` is not enough when a typed escape route remains live and
unaccounted.

#### Restoration-Recoil Subtypes

`restoration-recoil` is a typed escape-route family, not a generic objection bucket. When it is
listed in `escape_routes_checked[]`, the witness must include a canonical `subtype`. The
v0.4.3.0 subtype set is:

```text
restoration_recoil_subtypes = {
  fitrah-recoil,             -- resistance to fitrah/ground-state reorientation
  authority-return-recoil,   -- return to source prestige or hidden authority order
  worship-frame-recoil,      -- recoil against the restored worship/orientation frame
  scope-protest,             -- protest that scoped closure is not global exhaustion
  uptake-guarantee-recoil    -- demand that language guarantee interlocutor uptake
}
```

Live restoration-recoil subtypes must either be carried honestly as `held`, `PARTIAL`,
`LoopBreak`, or `non-load-bearing`, or be routed to an owner family licensed for that subtype:

```text
fitrah-recoil            -> P1 or R2
authority-return-recoil  -> source-status-repair or authority-order-repair
worship-frame-recoil     -> P1, R2, or P7
scope-protest            -> P7 or M8
uptake-guarantee-recoil  -> P7 plus the T_lang boundary
```

This is the C.5 restoration-recoil taxonomy only. It does not introduce the C.6 two-track
`primary|restoration` field, does not extend the collapse-certificate schema, and does not claim
that language delivery guarantees interlocutor uptake.

#### Two-Track Primary/Restoration MRP

After restoration-recoil is typed, generated burdens must also preserve which closure track they
belong to. `B_LA` burdens are implicitly on the primary track. Every `B_MRP` burden records:

```text
generated_burdens[].track = primary | restoration
```

`primary` means the generated burden is still needed to land the original noetic deformation.
`restoration` means the generated burden arose from the restorative move itself, usually through
a live `restoration-recoil` escape-route entry after `Land(Bk) -> R(H,Delta)`.

The graph-completeness checker evaluates the tracks separately:

```text
primary_track_closed      iff every primary-track burden is landed or honestly HOLD/PARTIAL/RECURSE
restoration_track_closed  iff every restoration-track burden is landed or honestly HOLD/PARTIAL/RECURSE
collapse_positive         requires no silent live burden on either track
```

A restoration-track generated burden must be backed by live `restoration-recoil`
generated-route evidence, unless it is explicitly held, partial, or proven non-load-bearing. A
primary-track burden cannot discharge a restoration recoil by being counted only as part of the
original claim track. The B.2 certificate fields `primary_track_closed` and
`restoration_track_closed` are a later certificate-schema lane; C.6 establishes the field-witness
and B.1 checker semantics.

#### `∇·B` / `∇×κ` Generated-Burden Consequence Rules

The post-Land divergence and curl diagnostics are control predicates. They are not decorative
notations printed beside an already chosen route. After `Land(Bk) -> R(H,Delta)`, the field state
constrains the next legal transition:

```text
positive or non-neutral ∇·B
  -> generated_burden_instantiation
  -> held_burden_activation
  -> HOLD / PARTIAL / RECURSE with source named
  -> or explicit non-load-bearing proof

non-null or held ∇×κ
  -> LoopBreak(∇×T) with licensed ground
  -> HOLD / PARTIAL / RECURSE with cycle named
  -> or explicit non-load-bearing proof
```

Thus `STOP` / `no_new_resultant` is legal only when the current burden-field divergence is neutral
and the curl state is null or resolved, unless the witness explicitly proves that the residual
pressure is non-load-bearing for this traversal. A positive `∇·B` at STOP is hidden divergence. A
non-null `∇×κ` without LoopBreak, HOLD/PARTIAL/RECURSE, or non-load-bearing proof is hidden curl.

If `LoopBreak` fires but the post-break reread still names non-null or unresolved curl, the route
must carry the residual cycle as HOLD/PARTIAL/RECURSE. It may not claim the curl is resolved while
the field still reports live circular pressure. The structured terminal checklist for every
`no_new_resultant` state is the C.8 terminal proof below.

#### Structured `no_new_resultant` Terminal Proof

A terminal `STOP` / `no_new_resultant` state must not be a confident sentence that substitutes for
field traversal. In the graph-completeness proof surface, the terminal formal reread state carries
a machine-readable proof object:

```json
{
  "no_new_resultant_proof": {
    "escape_routes_checked": [
      {"type": "closure-boundary-immunity", "live": false, "basis": "..."},
      {"type": "proof-carousel", "live": false, "basis": "..."},
      {"type": "total-system-exhaustion", "live": false, "basis": "..."},
      {"type": "doubt-churn", "live": false, "basis": "..."},
      {"type": "moral-tribunal", "live": false, "basis": "..."},
      {"type": "authority-order-recoil", "live": false, "basis": "..."},
      {"type": "hidden-framework-recoil", "live": false, "basis": "..."},
      {"type": "restoration-recoil", "subtype": "scope-protest", "live": false, "basis": "..."}
    ],
    "field_state_at_stop": {
      "divergence": "neutral",
      "curl": "null",
      "b_live": "empty",
      "kappa_residual": 0
    },
    "stop_licensed": true
  }
}
```

The proof object has three obligations:

1. Every canonical escape-route type is checked exactly once. A route marked `live: false` needs a
   named basis; a route marked `live: true` must point to generated-burden, held, HOLD/PARTIAL,
   RECURSE, LoopBreak, or non-load-bearing evidence already represented in the trace.
2. `field_state_at_stop` must agree with the formal state and the field diagnostics:
   divergence is neutral, curl is null or resolved, `B_live` is empty, and `kappa_residual` is `0`.
3. `stop_licensed` must be true. The license is earned by the structured field proof, not by the
   model's closure prose.

This keeps C.2/C.3 `escape_routes_checked[]` useful as optional state-local evidence while C.8
hardens the terminal STOP condition itself.

### Formalism-Emergent Escape-Route Closure

Escape-route closure is not licensed by pre-voicing likely objections. A route becomes live only
after the runtime lands the current burden and rereads the resulting state:

```text
Land(Bk)
  -> R(H,Delta)
  -> evaluate B_live, kappa, Reg, Routes
  -> detect live escape_routes(D0, traversal)
  -> generate B_MRP, route HOLD/PARTIAL/RECURSE, LoopBreak, or prove non-load-bearing
```

Thus a live `escape_routes_checked[]` entry must cite post-Land state evidence: the landed delta,
the `R(H,Delta)` reread, the route-gradient, divergence/curl state, live register pressure, or a
graph/commitment/framework pressure that appears after the delta. A stock list such as "the user
might object" or "likely reply" is not an MRP resultant. It becomes checkable only when the
post-Land state shows that the route is live and the witness records how it was generated, held,
bounded, or dismissed as non-load-bearing.

### Collapse-Positive Restoration Proof

Define `controlling_misread(S)` over the runtime state `S` as true when some live or hidden burden,
dependency, register pressure, route loop, or source/order deformation still governs the execution
field after traversal. In the current schema-light proof surface, that means at least one of these
holds: terminal accounting is incomplete, `∇·B` remains non-neutral, `∇×κ` remains non-null and
unresolved, or live material is neither landed nor honestly held as PARTIAL/RECURSE.

Within the scoped runtime execution field:

```text
controlling_misread(S) = false
  iff coverage_complete
      and ∇·B = neutral
      and ∇×κ in {null, resolved}
  iff collapse_positive(S)
```

The forward direction holds because if no governing misread remains, every diagnosed burden is
terminally accounted, no outward burden pressure remains, and no unresolved circular dependency
controls the route. The reverse direction holds by the definitions of coverage completeness, the
MRP Exhaustion Lemma, and curl resolution: there is no silent burden, no live generated pressure,
and no unresolved loop left with control of the runtime field.

The endpoint `N_fiṭrī ∧ ʿaql ṣarīḥ` is therefore a restoration claim about the runtime-side
orientation of the response: the obstructing misread no longer governs the field, so the response
can be released from the fitri/sound-reason orientation rather than from the defeated frame. This
does not install belief in the interlocutor, prove uptake, or claim access to the soul. By the
`T_lang` partiality proof, the public response is a partial coupling attempt from the completed
runtime field toward the diagnosed interlocutor field.

## Adjudication Summary

Implemented now:

- `𝓝`, `D₀`, `Ψᴺ`, and `N∈𝓝` as signal-state / noetic-selection bridge terms.
- `♥`, `ξ`, `Ω`, `μ`, `κ`, and `Δκ` as derived/conditional registers over existing IR,
  hold/release, collapse-radius, owner, reread, and restoration controls.
- `ⁿB`, `ⁿBᵢ`, `ΔⁿB`, `ⁿ⁺¹B`, `ⁿBᵢ[OP]`, and expanded `R(...)` as burden/governance notation.
- plain `∇` as a route-gradient read over eligible live pressure, constrained by IR/routing/owner gates.
- `∇·T` and `∇×T` as post-Delta, target-explicit field diagnostics
  over the Δ-produced noetic/burden/dependency/register/route/collapse field.
- `LoopBreak(∇×T)` as the explicit loop-breaking submove form when nonzero curl is owner-licensed for resolution.
- `𝒞(Ψᴺ)` and `N_fiṭrī ∧ ʿaql ṣarīḥ` as the positive closure-field condition after burden landing and reread.
- `Ψᴵ` and `T_lang: Ψᴺ ⇢ Ψᴵ` as the diagnosed interlocutor field and language-mediated public output boundary.
- Shannon analogy boundaries and anti-symbol-theater / anti-schema-bloat guards.

Outside this formalism surface:

- Hard mandatory schema fields for `heart`, `xi`, `Omega`, `mu`, or `kappa`.
- release, package, or tag claims.

Hard schema migration requires deliberate schema/checker/fixture/smoke migration and authorization.
Static fixtures prove the derived bridge against current controls; they are not a substitute for
release provenance or package-bound evidence.

Rejected as runtime behavior:

- Symbol theater: printing algebra that does not change execution.
- Algebra without owner/TTP operation.
- `κ` as a generic TODO list.
- `μ` as mere rhetoric.
- Omitted `ξ` where warrant/testimony/proof grammar is live.
- `Ω` as only a "metaphysics topic."
- `ΔⁿB` / `ⁿ⁺¹B` conflation.
- Shannon entropy as truth, meaning, warrant, fitrah, revelation, or restoration metric.

## Symbol Table

| Symbol | ASCII fallback | Meaning | Current status | Runtime mapping |
|---|---|---|---|---|
| `𝓝` | `N_space`, `mathcal-N` | Noetic-structure selection space | Implemented bridge | Design/read domain; not a schema field. |
| `D₀` | `D0` | Surface discourse / input signal | Implemented bridge | Input before diagnostic reduction. |
| `Ψᴺ` | `PsiN` | Encoded noetic signal-state | Implemented bridge | Reconstructed signal-state represented through IR/case-state. |
| `Ψᴵ` | `PsiI` | Diagnosed interlocutor noetic field | Implemented bridge | Inferred from discourse/profile/register evidence; not access to the soul or guaranteed uptake. |
| `T_lang: Ψᴺ ⇢ Ψᴵ` | `T_lang: PsiN -> PsiI` | Language-mediated public output boundary | Implemented bridge | Released response may perturb the diagnosed interlocutor field without claiming control of guidance. |
| `N∈𝓝` | `N in N_space` | Runtime-selected or held noetic frame | Implemented bridge | Current `N` is selected/held; family label is not warrant. |
| `IR(N,m,τ,σ)` | `IR(N,m,tau,sigma)` | Compact Diagnostic IR | Current canon | Required runtime dispatch bottleneck. |
| `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` | `IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)` | Expanded register bridge | Implemented bridge | Derived functions; not mandatory schema fields. |
| `♥` | `heart` | Affective-discursive register / release posture | Implemented bridge | Hold, sequence, tone, softness, directness, closure posture. |
| `ξ` | `xi` | Epistemic/warrant grammar | Implemented bridge | Evidence, testimony, proof-method, authority, defeater, proper function. |
| `Ω` | `Omega` | Ontological/predication grammar | Implemented bridge | Being, predication, modality, dependence, creator/creation distinction. |
| `μ` | `mu` | Meta-noetic memetic vector | Implemented bridge | Carrier, compression, stabilizer, defensive move, mutation/reproduction pattern. |
| `κ` | `kappa` | Collapse radius / downstream dependency set | Implemented bridge | Dependent claims/routes to reread; not a TODO list. |
| `Δκ` | `Delta-kappa` | Dependency-radius delta | Implemented bridge | Reread input after burden landing. |
| `ⁿB` | `nB` | n-th live burden-cycle | Implemented bridge | Current live burden with cycle index where needed. |
| `ⁿBᵢ` | `nBi` | i-th operative submove | Current canon | Owner-backed target -> operation -> result. |
| `ΔⁿB` | `Delta-nB` | Local landed state change | Implemented bridge | Local burden delta before reread. |
| `ⁿ⁺¹B` | `n-plus-1B` | Next burden-cycle | Implemented bridge | Licensed only after `Land(ⁿB) -> R(H,Delta)`. |
| `ⁿBᵢ[OP]` | `nBi[OP]` | Operator signature | Implemented bridge | `target -> operation -> result -> Delta-nB / Delta-kappa`. |
| `∇` | `route-gradient`, `gradient` | Route-gradient read over live field pressure | Implemented bridge | Orders eligible routes/burdens by expected diagnostic reduction or closure progress; constrained by IR/routing/owner gates. |
| `∇·T` | `del-dot(T)` | Divergence-like residual outward pressure in explicit target field `T` | Implemented bridge | Post-Delta closure diagnostic; target may be `κ`, `B`, `ξ`, `♥`, route/register/noetic field when owner-defined. |
| `∇×T` | `del-cross(T)` | Curl-like circularity / rotational dependency in explicit target field `T` | Implemented bridge | Post-Delta closure diagnostic; nonzero circulation must be broken, held, discharged, or carried into RECURSE/PARTIAL. |
| `LoopBreak(∇×T)` | `LoopBreak(del-cross(T))` | Loop-breaking submove over target field `T` | Implemented bridge | When licensed, grounds a circular dependency in an owner-bound non-circular source, produces Δ, and rereads `∇×T`. |
| `R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)` | `R(H, Delta-nB{heart,xi,Omega,sigma,mu}, Delta-kappa)` | Expanded reread gate | Implemented bridge | Current `R(H,Δ)` plus live register/dependency deltas; `R(H,Delta)` remains ASCII fallback. |
| `𝒞(Ψᴺ)` | `C(PsiN)` | Positive closure-field condition over the agent execution field | Implemented terminal formalism | Endpoint only when live pressure is landed, integrated, discharged, held, or carried into PARTIAL/RECURSE. |
| `N_fiṭrī ∧ ʿaql ṣarīḥ` | `N_fitri and aql_sarih` | Fitri/sound-reason restorative orientation | Implemented terminal formalism | Telos after governing misread loses control; not a shortcut marker. |

## Runtime Boundary

The bridge is live only through control effect. A symbol is operative when it changes at least
one of these:

- an existing IR/case-state feature,
- owner/TTP eligibility,
- held material,
- hold/release posture,
- burden selection,
- collapse radius,
- `Land(ⁿB)` or `R(H,Δ)`,
- terminal restoration boundary.

If a symbol does not change those controls, it belongs in this spec or an audit explanation,
not in default runtime output. The default user-facing render remains compact and does not print
raw `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` unless the user asks for formalism or `:dsl` / audit visibility.

## Route-Gradient / Delta / Divergence / Curl Operator Distinction

Plain `∇` is the route-gradient operator over the live noetic/burden/dependency/register/route
field. It reads the direction of steepest live pressure change: the eligible route or burden
whose release is expected to produce the greatest diagnostic reduction, closure progress, or
dependency clarification. It is a routing pressure read, not an unconstrained intuition. IR,
V1/routing precedence, owner catalogue eligibility, source-status, and held-material gates still
bound the route set. Plain `∇` does not prove truth or warrant, does not replace `Delta-nB` or
`Delta-kappa`, does not replace `∇·` or `∇×`, and does not force a single deterministic route
when multiple valid structures remain live.

`Delta-nB` is the burden-event delta: the local landed state change after a bounded owner/TTP
operation. `Delta-kappa` is the dependency-radius delta consumed by `R(H,Δ)` before
STOP/HOLD/PARTIAL/RECURSE. These are event-local transition operators.

The field-level operators are different. `∇·` (checker/search aliases: del-dot, del dot, nabla dot, divergence)
reads the noetic/burden/dependency/register/route field after one or more delta events and asks
whether pressure is expanding, contracting, or neutral across the selected field target. Positive
divergence means the landed burden exposes more live pressure; negative divergence means
dependency pressure contracts toward closure; zero divergence means no meaningful control change.
If `∇·κ` remains positive/live, STOP/COMPLETE is not licensed. `κ` is the common
collapse/closure-state target, but it is not the only valid target and the operators are not
restricted to `κ`: a burden, dependency, route, register, or noetic-field target may be read when
the target is explicit and owner-defined.

`∇×` (checker/search aliases: del-cross, del cross, nabla cross, curl) reads circulation in that same field after delta
events. It asks whether warrant, ontology, discourse state, affective posture, memetic carrier,
dependency radius, burden order, or route relation loop back into one another. Standard curl is
a 3D construction; this repo uses it only as a formal analogy for antisymmetric / circular
dependency pressure over an owner-defined target field. It is not decorative physics and does not
claim discourse is literally a physical field. If nonzero curl remains live, the output must break
the loop or mark PARTIAL/RECURSE; answering one local proposition does not discharge a curl-like
dependency loop.

Neither `∇·` nor `∇×` replaces `Delta-nB` or `Delta-kappa`. Delta operators are computed at burden
events. Divergence/curl read the field that delta events have produced across the whole
noetic/burden/dependency/register/route space. These operators do not apply to a scalarized
one-point master diagnosis; they apply only after the runtime preserves a live field with an
explicit target and control effect. Scalar collapse is an execution failure because the field is
lost when noetic structure is reduced to a one-point summary. Default governed output must use
target-explicit compact markers such as `∇·κ`, `∇×κ`, `∇·B`, `∇×B`, `∇·♥`, or `∇×ξ` when the field
diagnostic is control-relevant; it must not dump long formalism exposition unless the user
requested formalism/audit visibility. Control effects include dependency pressure,
loop-breaking, `R(H,Δ)`, HOLD/PARTIAL/RECURSE/COMPLETE, or checker outcome.

If `∇×T` remains nonzero, `LoopBreak(∇×T)` is the explicit loop-breaking submove form. The
runtime must either license a loop-breaker or hold/recurse/partial the loop with reason. A valid
loop-breaker names the target loop, grounding source, burden/submove, `Δ` effect, post-break
`∇×T` reread, and closure/hold result. Owner-licensed grounds include fiṭrah, `ʿaql ṣarīḥ`,
necessary knowledge, direct contradiction exposure, definition discipline, source-status
correction, or doubt-churn boundary. The machine vocabulary is closed:
`fitrah_ground`, `sound_reason_ground`, `necessary_knowledge`,
`direct_contradiction_exposure`, `definition_discipline`, `source_status_correction`, and
`doubt_churn_boundary`. It is invalid to use loop-breaking as arbitrary assertion or to invoke an
open-ended "another non-circular owner ground" without one of these licensed grounds.

`𝒞(Ψᴺ)` is the positive closure-field condition over the agent execution field. It is not simply
"no checklist item remains." The field must reach the target configuration: burdens landed or
integrated, live material held or partialed with reason, residual `∇·` neutral/bounded, residual
`∇×` resolved or explicitly held, and the route from diagnosis to restoration reconstructable
without hidden live pressure. It does not mean the interlocutor has accepted truth.

`Ψᴺ` and `Ψᴵ` are distinct. `Ψᴺ` is the agent/runtime execution field. `Ψᴵ` is the diagnosed
interlocutor noetic field inferred from discourse, profile, register, response, and source-status
evidence. `T_lang: Ψᴺ ⇢ Ψᴵ` names the language-mediated coupling attempt produced by release; it
does not claim access to the soul, guaranteed uptake, total profile identity, or agent control of
guidance.

`Ψᴵ` remains uncertainty-bearing. Where the discourse basis is thin or compatible with multiple
candidate noetic structures, the runtime should hold alternatives through `read_status`,
`confidence`, `decisive_missing_differentiator`, `what_remains_live`, or route notes rather than
certifying a single interlocutor field. This is still schema-light: uncertainty may be compact, and
ordinary output should not grow a decorative uncertainty paragraph.

### T_lang Partiality Proof

`T_lang: Ψᴺ ⇢ Ψᴵ` is partial by the state definition. `Ψᴺ` is the runtime-accessible execution
field: the system can inspect its selected/held `N`, live burdens, owner routes, deltas,
diagnostics, closure state, and rendered response. `Ψᴵ` is not directly accessible; it is inferred
from public discourse, profile signals, register evidence, source-status evidence, and later
responses. The release step emits natural language into a public channel that may be misunderstood,
refused, ignored, reframed, or answered from a different held structure.

Therefore `T_lang` cannot be a total function from runtime closure to interlocutor update. It also
cannot be an isomorphism, because the runtime's internal proof graph and the interlocutor's noetic
field do not expose the same state space. It is not a surjection, because many possible
interlocutor states are not reachable by one response and some are not under the runtime's control
at all. The release claim is only that the response is structured to carry the completed
`Ψᴺ` perturbation honestly. It is not a claim of soul access, guidance control, guaranteed uptake,
or exhaustive model identity.

The diagnostic is operative only when it changes owner/TTP eligibility, held material,
hold/release posture, burden selection, dependency radius, `R(H,Δ)`, PARTIAL/RECURSE/COMPLETE,
or checker outcome. It is symbol theater if it merely decorates an audit or appears without a
control effect. Shannon language remains bounded to signal, encoding, channel constraint,
noise/distortion, redundancy/error correction, and capacity/compression-loss analogies; it never
measures truth, meaning, warrant, revelation, fitrah, or sound reason.

## Divergence / Curl Diagnostic Boundary

Runtime notation forms: `∇·T` and `∇×T`. Checker/search aliases include `del-dot`, `del dot`, `del-cross`, `del cross`, `nabla dot`,
`nabla cross`, `divergence`, and `curl`; they are not separate runtime operators. In default runtime output, compact Unicode markers
must appear when control-relevant in target-explicit state notation such as `State: Δκ live;
∇·κ positive; ∇×κ unresolved; R(H,Δ): RECURSE.`, `Burden field: ΔⁿB landed; ∇·ⁿB positive over
dependent burdens; ∇×ⁿB unresolved around compact-neutrality dependency.`, or `Register field: ∇·♥
positive; ∇×ξ unresolved; R(H,Δ): HOLD.` ASCII aliases and long explanations are not default
notation unless the user asks for algebra/formalism/audit visibility. In audit/formalism
surfaces, all forms are allowed only with the operator distinction and control-effect rule above.

## Correct Use

- Use `ξ` only when warrant, testimony, proof-method, authority, evidence, proper function, or
  defeater grammar changes routing, release, or reread.
- Use `Ω` only when being, predication, modality, dependence, causality, or creator/creation
  grammar changes the operator or burden.
- Use `μ` only when a recurring slogan, carrier, identity stabilizer, compression, defensive
  move, or mutation changes an existing control surface.
- Use `κ` to name the downstream dependency set that must be reread after a load-bearing node
  changes.
- Use `ΔⁿB` for local burden-state change and `ⁿ⁺¹B` only for a new burden licensed after
  `Land(ⁿB) -> R(H,Delta)`.
- Keep every `ⁿBᵢ[OP]` attached to target -> operation -> result.

## Compositional Noetic-State Boundary

Stage 8 hardening treats the implemented child-mode families as compositional owner surfaces,
not isolated operator tables. The schema-light control grammar is:

```text
N_space read
-> selected/held N_frame
-> NS intervention profile
-> PF / pattern_profile
-> live register set {heart, xi, Omega, mu, kappa, sigma}
-> owner/TTP child mode
-> Land(ⁿB)
-> R(H,Delta)/kappa
```

`unknown-pattern-typed` is valid when the case is too thin for a named `NS` profile but still
contains typed operator pressure. In that state, the runtime may route by M9/PM/AS/DW/DA/DS/HK/
OQ/MM behavior while keeping the named noetic frame held. This is not a hard schema migration:
the registers remain derived control lenses over existing IR/case-state fields.

## Incorrect Use

- Printing `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` while the response acts like a generic essay.
- Treating `♥` as mood labeling or motive speculation.
- Treating `κ` as "more things to address."
- Treating `μ` as rhetorical color.
- Treating `Ω` as any theology topic instead of ontology/predication grammar.
- Omitting `ξ` in a proof-demand, testimony, source-authority, or warrant-governed case.
- Using `ⁿ⁺¹B` for every topic shift.
- Treating `ΔⁿB` and `ⁿ⁺¹B` as interchangeable.

## NLA / Shannon Analogy Boundary

Useful analogy:

- signal versus encoding,
- channel constraints,
- noise and distortion,
- redundancy and error correction,
- capacity and compression loss.

Do not claim:

- Shannon entropy measures truth,
- information theory measures meaning,
- lower entropy means better warrant,
- noetic restoration is literal channel correction,
- fitrah, revelation, or sound reason are reducible to statistical signal properties.

The analogy is a visual and engineering discipline: the input signal must be encoded without
losing the governing noetic function, and the runtime must correct distortion by restoring the
right warrant/order. It is not an ontology of truth.

NLA means Natural Language Autoencoder in the narrow audit analogy: an activation verbalizer
maps activation to natural-language explanation, and an activation reconstructor maps the
explanation back to a reconstructed activation. In this repo, the daee analogue is Layer A /
Diagnostic IR / noetic-field banner as verbalizer and IR reconstruction / `R(H,Delta)` as
reconstructor. NLA is not generic linear algebra, nonlinear architecture, Shannon theory, or
activation-level proof. It may describe whether a natural-language diagnostic bottleneck
reconstructs the governed noetic state, but it does not prove that vectors, entropy, FVE,
residual stream language, or linear algebra measure truth, meaning, warrant, revelation,
fitrah, or sound reason. The complete algebraic-symbol operativity inventory is audited in
`docs/audits/v0.4.1.0-algebraic-symbol-operativity-audit.md`; the separate NLA fidelity gate is
audited in `docs/audits/v0.4.1.0-nla-operativity-audit.md`.

## Checker and Smoke Implications

Current checks must prove both sides of the bridge:

- v0.3.2.0 compact runtime behavior still passes;
- the accepted register-formalism symbols live in atomics/spec/index, not only `docs/index.html`;
- hard register fields are not silently added to Diagnostic IR schema;
- notation is forbidden when it does not change owner selection, hold/release, burden delta,
  reread, or restoration;
- terminal formalism cannot bypass closure audit, P1/P7, M1/M1-P, M9, source-local operation,
  or no-detached-source-stack-compression requirements.

Hard schema promotion still requires positive and negative fixtures, hard smokes, version
marker migration, and release review.

## Source Of Truth

Canonical runtime rules are authored in `atomics/skill/**` and compiled into generated `skill/**`.
This document preserves the algebra and maps it to the current derived bridge. The full item
ledger lives in [`register-formalism-implementation-ledger.md`](register-formalism-implementation-ledger.md).
`docs/index.html` is a rich navigation/control-wiki surface; it is not the sole source of
runtime or theory invariants.
