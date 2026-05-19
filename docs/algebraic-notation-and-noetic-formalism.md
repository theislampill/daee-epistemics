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
correction, or another non-circular owner ground. It is invalid to use loop-breaking as arbitrary
assertion.

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
