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
Input -> IR(N,m,tau,sigma) -> B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

schema-light register bridge baseline:

```text
𝓝 ⊢ D₀ ⇝ Ψᴺ<N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H>
→ IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
→ [ⁿB → {ⁿBᵢ[OPᵢ]} → Land(ⁿB) → R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)]*
→ 𝒞(Ψᴺ) → N_fiṭrī ∧ ʿaql ṣarīḥ / ⁿ⁺¹B
```

ASCII fallback:

```text
N_space |- D0 ~> PsiN<N in N_space,m,tau,sigma,heart,xi,Omega,mu,kappa,H>
-> IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)
-> [nB -> {nBi[OPi]} -> Land(nB) -> R(H,Delta-nB{heart,xi,Omega,sigma,mu},Delta-kappa)]*
-> C(PsiN) -> N_fitri and aql_sarih / n-plus-1B
```

## Adjudication Summary

Implemented now:

- `𝓝`, `D₀`, `Ψᴺ`, and `N∈𝓝` as signal-state / noetic-selection bridge terms.
- `♥`, `ξ`, `Ω`, `μ`, `κ`, and `Δκ` as derived/conditional registers over existing IR,
  hold/release, collapse-radius, owner, reread, and restoration controls.
- `ⁿB`, `ⁿBᵢ`, `ΔⁿB`, `ⁿ⁺¹B`, `ⁿBᵢ[OP]`, and expanded `R(...)` as burden/governance notation.
- `𝒞(Ψᴺ)` and `N_fiṭrī ∧ ʿaql ṣarīḥ` as terminal formalism after burden landing and reread.
- Shannon analogy boundaries and anti-symbol-theater / anti-schema-bloat guards.

Still deferred with blocker:

- Hard mandatory schema fields for `heart`, `xi`, `Omega`, `mu`, or `kappa`.
- v0.4.0.0 contract/release migration.

Blocker: hard schema and release migration require deliberate schema/checker/fixture/smoke
migration, reviewed fresh hard smokes, and release authorization. Static fixtures prove the
derived bridge against current controls; they are not a substitute for package-bound live smokes.

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
| `ⁿ⁺¹B` | `n-plus-1B` | Next burden-cycle | Implemented bridge | Licensed only after `Land(B) -> R(H,Delta)`. |
| `ⁿBᵢ[OP]` | `nBi[OP]` | Operator signature | Implemented bridge | `target -> operation -> result -> Delta-nB / Delta-kappa`. |
| `R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)` | `R(H, Delta-nB{heart,xi,Omega,sigma,mu}, Delta-kappa)` | Expanded reread gate | Implemented bridge | Current `R(H,Δ)` plus live register/dependency deltas; `R(H,Delta)` remains ASCII fallback. |
| `𝒞(Ψᴺ)` | `C(PsiN)` | Constrained noetic collapse / discursive resolution | Implemented terminal formalism | Endpoint after landing, held-route reread, and decision. |
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
- `Land(B)` or `R(H,Δ)`,
- terminal restoration boundary.

If a symbol does not change those controls, it belongs in this spec or an audit explanation,
not in default runtime output. The default user-facing render remains compact and does not print
raw `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` unless the user asks for formalism or `:dsl` / audit visibility.

## Delta / Divergence / Curl Operator Distinction

`Delta-nB` is the burden-event delta: the local landed state change after a bounded owner/TTP
operation. `Delta-kappa` is the dependency-radius delta consumed by `R(H,Δ)` before
STOP/HOLD/PARTIAL/RECURSE. These are event-local transition operators.

The field-level operators are different. `∇·` (del-dot, del dot, nabla dot, divergence)
reads the noetic/burden/dependency/register/route field after one or more delta events and asks
whether pressure is expanding, contracting, or neutral across the selected field target. Positive
divergence means the landed burden exposes more live pressure; negative divergence means
dependency pressure contracts toward closure; zero divergence means no meaningful control change.
If `∇·κ` remains positive/live, STOP/COMPLETE is not licensed. `κ` is the common
collapse/closure-state target, but it is not the only valid target and the operators are not
restricted to `κ`: a burden, dependency, route, register, or noetic-field target may be read when
the target is explicit and owner-defined.

`∇×` (del-cross, del cross, nabla cross, curl) reads circulation in that same field after delta
events. It asks whether warrant, ontology, discourse state, affective posture, memetic carrier,
dependency radius, burden order, or route relation loop back into one another. Standard curl is
a 3D construction, but the high-dimensional analogue used here is the antisymmetric part of the
Jacobian / exterior derivative: a noetic-state field over `N_space` can have circular dependency
pressure without being a 3D physical field. If nonzero curl remains live, the output must break
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

The diagnostic is operative only when it changes owner/TTP eligibility, held material,
hold/release posture, burden selection, dependency radius, `R(H,Δ)`, PARTIAL/RECURSE/COMPLETE,
or checker outcome. It is symbol theater if it merely decorates an audit or appears without a
control effect. Shannon language remains bounded to signal, encoding, channel constraint,
noise/distortion, redundancy/error correction, and capacity/compression-loss analogies; it never
measures truth, meaning, warrant, revelation, fitrah, or sound reason.

## Divergence / Curl Diagnostic Boundary

Allowed forms: `∇·`, `∇×`, `del-dot`, `del dot`, `del-cross`, `del cross`, `nabla dot`,
`nabla cross`, `divergence`, and `curl`. In default runtime output, compact Unicode markers
must appear when control-relevant in target-explicit state notation such as `State: Δκ live;
∇·κ positive; ∇×κ unresolved; R(H,Δ): RECURSE.`, `Burden field: ΔⁿB landed; ∇·B positive over
B3/B4; ∇×B unresolved around compact-neutrality dependency.`, or `Register field: ∇·♥
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
  `Land(B) -> R(H,Delta)`.
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
-> Land(B)
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
