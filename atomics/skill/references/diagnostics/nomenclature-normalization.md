---
id: nomenclature-normalization
module_class: governance
canonical_path: skill/references/diagnostics/nomenclature-normalization.md
contract_version: "0.3.2.0"
load_when:
  - release or maintainer review needs canonical naming for noetic state, DSL/IR, TTP, owner, or optional route/check harness terms
  - a term alias could affect routing, proof denominator, render governance, or public release claims
emits:
  - nomenclature_normalization
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

# Nomenclature Normalization

This file fixes names. It does not add routes, owners, IR fields, PF codes, source-basis
categories, codons, or a second DSL. When a code key already exists, preserve the ASCII key
and treat readable theological forms as prose aliases.

## Noetic-State Notation

| Canonical term | Accepted aliases | Status |
|---|---|---|
| `N_AT` | `N_Athari`, `N_Salafi`, `N_Taymiyyan`, `N_Wahhabi`, `N_Atharī`, `N_Salafī`, `N_Wahhābī` | Documentation shorthand for one Atharī/Salafī/Taymiyyan/Wahhābī noetic frame family; not multiple warrants. |
| `N_Ashari` | `N_Ash'ari`, `N_Ashʿarī`, `Ashari family`, `Ashʿarī family` | Family label only. Do not flatten variants into one operative noetic state when a case requires distinction. |
| `N_Maturidi` | `N_Māturīdī`, `Maturidi family`, `Māturīdī family` | Family label only. Do not flatten variants into one operative noetic state when a case requires distinction. |
| `N_kalamic_evidentialist` | `kalāmic evidentialist`, `kalamic evidentialist` | Operative profile shorthand when the proof-status burden, necessary-knowledge boundary, or naẓar demand is live. |
| `N_theistic_evidentialist` | `theistic evidentialist` | Operative profile shorthand when the interlocutor is theistic but routes warrant primarily through evidentialist proof demand. |
| `NS-*` | `noetic-state profile code` | Profile/support shorthand. It is not by itself an operative TTP or proof-denominator owner. |

These symbolic forms are compact routing and documentation notation. Public output should not
brand the interlocutor with a code unless diagnostic render or user request makes it useful.

## ʿAqīdah Family Terms

- Canonical readable family: `Atharī/Salafī`.
- Accepted aliases: `Atharī`, `Salafī`, `Taymiyyan`, `Wahhābī`; ASCII aliases
  `Athari`, `Salafi`, and `Wahhabi` are code/search-friendly variants.
- Routing normalization: these aliases can identify the same broad noetic frame family for
  internal normalization. They do not create a public source parade or named-school proof.
- `Ashʿarī` and `Māturīdī` name varied families, not monoliths. If a case turns on a
  particular subfamily, premise, proof method, or taʾwīl rule, preserve that distinction.
- Pattern and deformation outrank school/source label: `Pattern > denomination/source-label`.

## Kalām / Speculative Theology Terms

- Canonical English label for `kalām`: `Speculative Theology`.
- Accepted prose aliases: `kalām`, `kalāmic`, `speculative-theological`, and
  `speculative-theological schools`; ASCII `kalam` / `kalamic` remain code/search aliases.
- Do not use `Rational Theology` as the controlled label for kalām in operative,
  release-facing, or public documentation surfaces. If a historical quote uses rational-language,
  mark it as historical rather than making it the repo's terminology.
- `Ashʿarī` and `Māturīdī` remain varied speculative-theological families, not monoliths and
  not automatic operative noetic states.

## Scholarship / Source-Status Labels

- In operative source-status fields, reserve `Islamic scholar` and `Islamic scholarship`
  for Salafī/Atharī-aligned scholarship; do not use them as umbrella warrant labels.
- For non-Atharī kalām or falsafah figures, use specific labels such as `kalām theologian`,
  `speculative theologian`, `school theologian`, `Ashʿarī theologian`,
  `Māturīdī theologian`, `mutakallim`, `school authority`, `philosopher`, or
  `later theological figure`, as appropriate.
- This is source-status and noetic-frame discipline, not a public denunciation rule. Do not
  add polemical clutter, scholar/source parade, or authority-by-association branding.

## DSL/IR Terms

| Canonical field/term | Accepted aliases | Note |
|---|---|---|
| `Diagnostic IR` | `IR`, `typed IR` | Structured bottleneck for case state and routing. |
| `case_state` | `Case State` | Runtime/prose view of typed state; not a replacement for Diagnostic IR. |
| `typed noetic state` | `noetic state`, `N` | The diagnosed noetic frame, not a personal verdict. |
| `live_burden` | `live burden`, `B` | Current input-anchored burden. |
| `matched_modules` | `matched modules` | Module IDs selected by validated routing; labels alone are not execution. |
| `restoration_target` | `target restoration`, `what must land` | The state to restore or clear before release. |
| `deformation` | `noetic deformation` | The operative obstruction family. |
| `concealment_mode` | `mode of concealment` | How the obstruction hides or presents. |
| `discourse_orientation` | `orientation` | What the discourse is ordered toward. |
| `reconstruction_fidelity` | none | `pass`, `partial`, or `fail`; do not rename in schema/data. |
| `reconstructor_notes` | reconstruction notes | Brief note for partial/fail or compact neighbor contrast. |
| `post_render_gate` | post-render gate | STOP/HOLD/RECURSE/PARTIAL decision after Land(B) and state re-read. |

## Algebraic Formalism Terms

The expanded algebraic notation preserved in `docs/algebraic-notation-and-noetic-formalism.md`
is a Pipeline #2 theory/specification bridge over the current runtime. Its derived/conditional
control semantics are canonical when they change existing diagnosis, routing, hold/release,
collapse-radius, reread, or restoration behavior. It does not add routes, owners, mandatory
IR fields, PF codes, source-basis categories, schema keys, or a second DSL.

| Formal symbol | ASCII fallback | Status |
|---|---|---|
| `𝓝` | `N_space`, `mathcal-N` | Noetic-structure selection space; design-space notation, not a schema field. |
| `D₀` | `D0` | Surface discourse / input signal before diagnostic reduction. |
| `Ψᴺ` | `PsiN` | Encoded noetic signal-state; represented operationally through current IR/case-state. |
| `N∈𝓝` | `N in N_space` | Explanatory notation for the selected operative `N`; family labels still do not become warrant. |
| `♥` | `heart` | Affective-discursive register / release-posture notation; derived from existing hold/release and register-governance surfaces. |
| `ξ` | `xi` | Epistemic/warrant grammar: evidence, testimony, proof-method, authority, defeater, proper function. |
| `Ω` | `Omega` | Ontological grammar: being, predication, modality, dependence, creator/creation distinction. |
| `μ` | `mu` | Meta-noetic memetic vector; valid only when it changes an existing control surface. |
| `κ` | `kappa` | Collapse radius / downstream dependency set; not a generic TODO list. |
| `Δκ` | `Delta-kappa` | Dependency-radius delta consumed by state re-read. |
| `ΔⁿB` | `Delta-nB` | Local burden-state change; not the next burden-cycle. |
| `ⁿ⁺¹B` | `n-plus-1B` | Next burden-cycle licensed only after `Land(B) -> R(H,Delta)`. |
| `𝒞(Ψᴺ)` | `C(PsiN)` | Constrained noetic collapse / discursive resolution; architecture notation, not a default output marker. |

Expanded `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` is accepted as formal/spec notation for conditionally live
derived registers. Current hard schema remains `IR(N,m,τ,σ)`, but the derived bridge is current
runtime-adjacent canon: any live register must affect an existing IR field, owner choice,
hold/release decision, collapse radius, `Land(B)`, `R(H,Delta)`, or restoration boundary.

## Optional Route/Check Harness Terms

| Canonical term | Accepted aliases | Note |
|---|---|---|
| `feature` | `signal` when prose-only | Use `feature` in JSON and scripts. |
| `span-backed feature` | `span-backed signal` | A feature with original-input span support. |
| `deterministic feature` | `mechanical feature` | Regex/parser-derived local feature. |
| `LLM-assisted feature` | `span-backed interpretive slot` | Accepted only with span and confidence; can fall back to ambiguous. |
| `ambiguous fallback` | `ambiguous` | Low-confidence interpretive result that does not route. |
| `route_plan` | `route plan` | Binding optional route/check harness artifact. |
| `first_live` | `first-live` in prose | Code/API key remains `first_live`; prose may say first-live. |
| `continuation_queue` | `continuation queue` | Code/API key remains `continuation_queue`; prose may use spaced form. |
| `held` | `held owner`, `held route` | Not released in the current pass. |
| `deferred` | `deferred owner`, `yielded route` | Plausible neighbor delayed by precedence or first-live blocker. |
| `rejected` | `not routed` | Trigger conditions not satisfied. |
| `validation_report` | `validation.json` | Integrity and ontology licensing result. |
| `reconstruction_report` | `reconstruction.json` | Route reconstructibility result. |
| `execution_fidelity` | execution check verdict | Post-output validation result. |

The optional route/check harness gives deterministic routing given features. It does not claim
deterministic feature extraction or deterministic transformer execution. It is repo/dev/CI
machinery unless a maintainer explicitly requests it; it is not the canonical package identity
and not the ordinary scriptless runtime.

## TTP / Owner / Operator Terms

- `TTP`: the named technique/tactic/procedure pattern.
- `owner`: the file or compiled section that owns the TTP's execution floor.
- `operator`: the currently active runtime function when a TTP is actually doing work.
- `owner-floor`: owner-specific `target -> operation -> result` evidence.
- `submove`: one bounded operation inside the current burden.
- `ⁿBᵢ`: preferred public/governance shorthand for burden submoves (`¹B₁`, `¹B₂`, `²B₁`, ...).
  `1B1`, `1B2`, `2B1` are ASCII fallbacks; `B1.s1` / `B<N>.s<M>` are legacy/checker aliases.
- `Land(B)`: the landed state change for the current burden.
- `R(H,Delta)`: the state re-read after Land(B). ASCII `Delta` is canonical in code and
  checker text; the Greek delta form may appear in historical prose.

TTP, owner, and operator are not interchangeable in strict proof. A TTP may be selected, an
owner may be loaded, and an operator may execute. Strict execution requires owner-floor evidence
and Land(B)/R(H,Delta), not label presence.

## Transliteration

Use ASCII-friendly keys in code/YAML/JSON. In prose, readable transliteration may be used only
where the file encoding already supports it cleanly; release data and schema keys remain ASCII.

| Canonical prose | ASCII/code-friendly alias | Notes |
|---|---|---|
| `fiṭrah` | `fitrah` | Innate normative disposition; do not reduce to culture or mood. |
| `ḍarūrī` | `daruri` | Necessary/non-discursive knowledge. |
| `naẓarī` | `nazari` | Discursive/inferential reasoning. |
| `waḥy` | `wahy` | Revelation. |
| `shubhah` | `shubha`, plural `shubuhat` | Doubt/objection; do not route all objections as genuine shubhah before deformation/register checks. |
| `mushābara fāsida` | `mushabara fasida` | False resemblance; code/data use ASCII. |
| `ʿaqīdah` | `aqidah` | Creed/doctrinal frame. |
| `kalām` | `kalam` | Speculative Theology; do not use `Rational Theology` as the repo-controlled English label. |
| `ẓāhir` | `zahir` | Apparent/manifest wording; preserve the semantic gate before any ta'wil discussion. |
| `taʾwīl` | `tawil`, `ta'wil` | Interpretive turning; do not treat every explanation as licensed ta'wil. |
| `majāz` | `majaz` | Figurative usage claim; keep it distinct from haqiqah/haqiqi and from modality questions. |
| `ḥaqīqah` | `haqiqah` | Reality/literal truth claim; code/data use ASCII alias when needed. |
| `ḥaqīqī` | `haqiqi` | Real/literal qualifier; keep separate from merely emphatic prose. |
| `hawā` | `hawa` | Desire/inclination pressure; never infer interior motive without input anchor. |
| `gharaḍ` | `gharad` | Aim/purpose/agenda pressure; keep it input-anchored and governance-bounded. |
| `ʿāda` | `ada` | Habit/custom; distinguish habit-pressure from proof-status. |
| `iʿrāḍ` | `irad` | Turning away; ASCII key remains `irad` in code/data. |
| `juḥūd` | `juhud` | Denial after recognition; requires stronger evidence than ordinary disagreement. |
| `istikbār` | `istikbar` | Arrogant refusal; do not collapse into generic objection. |

## Smoke and Campaign Names

Named hard-smoke labels, named interlocutor labels, and comparison-standard labels are not
operative nomenclature. They may appear in fixtures, tests, smoke reports, and audit history.
Operative scripts, trigger-matrix rules, runtime governance, and public user-facing docs
should use genus-level terms such as `named source-worldview`, `imported criterion`,
`opponent worldview frame`, or `moral tribunal`.

## Release-Claim Boundary

The normalized release claim is:

- Default `/daee-epistemics` is the canonical compact DSL-governed runtime, not prose-only mode.
- `/daee-epistemics:dsl` is expanded diagnostic/IR visibility, not the first place DSL appears.
- The optional script-capable route/check harness is repo/dev/CI machinery, historically called
  Level 3, and is not canonical package content or the public identity of the skill.
- Maintainer-requested script-capable harness runs are deterministic in routing given extracted features.
- Feature extraction includes span-backed interpretive components and can vary.
- Transformer execution remains probabilistic and high-complexity render-through can still fail.
- Pure-Hermes parity, codons, owner packs, and catalogue-wide deterministic routing are not claimed.
