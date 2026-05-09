---
id: nomenclature-normalization
module_class: governance
canonical_path: skill/references/diagnostics/nomenclature-normalization.md
contract_version: "0.3.2.0"
load_when:
  - release or maintainer review needs canonical naming for noetic state, DSL/IR, TTP, owner, or Level 3 terms
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
| `N_AT` | `N_Athari`, `N_Salafi`, `N_Taymiyyan`, `N_Wahhabi` | Documentation shorthand for one Athari/Salafi/Taymiyyan/Wahhabi noetic frame family; not multiple warrants. |
| `N_Ashari` | `N_Ash'ari`, `Ashari family` | Family label only. Do not flatten variants into one operative noetic state when a case requires distinction. |
| `N_Maturidi` | `Maturidi family` | Family label only. Do not flatten variants into one operative noetic state when a case requires distinction. |
| `N_kalamic_evidentialist` | `kalamic evidentialist` | Operative profile shorthand when the proof-status burden, necessary-knowledge boundary, or nazar demand is live. |
| `N_theistic_evidentialist` | `theistic evidentialist` | Operative profile shorthand when the interlocutor is theistic but routes warrant primarily through evidentialist proof demand. |
| `NS-*` | `noetic-state profile code` | Profile/support shorthand. It is not by itself an operative TTP or proof-denominator owner. |

These symbolic forms are compact routing and documentation notation. Public output should not
brand the interlocutor with a code unless diagnostic render or user request makes it useful.

## Aqidah Family Terms

- Canonical readable family: `Athari/Salafi`.
- Accepted aliases: `Athari`, `Salafi`, `Taymiyyan`, `Wahhabi`.
- Routing normalization: these aliases can identify the same broad noetic frame family for
  internal normalization. They do not create a public source parade or named-school proof.
- `Ashari` and `Maturidi` name varied families, not monoliths. If a case turns on a
  particular subfamily, premise, proof method, or ta'wil rule, preserve that distinction.
- Pattern and deformation outrank school/source label: `Pattern > denomination/source-label`.

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

## Level 3 Terms

| Canonical term | Accepted aliases | Note |
|---|---|---|
| `feature` | `signal` when prose-only | Use `feature` in JSON and scripts. |
| `span-backed feature` | `span-backed signal` | A feature with original-input span support. |
| `deterministic feature` | `mechanical feature` | Regex/parser-derived local feature. |
| `LLM-assisted feature` | `span-backed interpretive slot` | Accepted only with span and confidence; can fall back to ambiguous. |
| `ambiguous fallback` | `ambiguous` | Low-confidence interpretive result that does not route. |
| `route_plan` | `route plan` | Binding Level 3 routing artifact. |
| `first_live` | `first-live` in prose | Code/API key remains `first_live`; prose may say first-live. |
| `continuation_queue` | `continuation queue` | Code/API key remains `continuation_queue`; prose may use spaced form. |
| `held` | `held owner`, `held route` | Not released in the current pass. |
| `deferred` | `deferred owner`, `yielded route` | Plausible neighbor delayed by precedence or first-live blocker. |
| `rejected` | `not routed` | Trigger conditions not satisfied. |
| `validation_report` | `validation.json` | Integrity and ontology licensing result. |
| `reconstruction_report` | `reconstruction.json` | Route reconstructibility result. |
| `execution_fidelity` | execution check verdict | Post-output validation result. |

Level 3 gives deterministic routing given features. It does not claim deterministic feature
extraction or deterministic transformer execution.

## TTP / Owner / Operator Terms

- `TTP`: the named technique/tactic/procedure pattern.
- `owner`: the file or compiled section that owns the TTP's execution floor.
- `operator`: the currently active runtime function when a TTP is actually doing work.
- `owner-floor`: owner-specific `target -> operation -> result` evidence.
- `submove`: one bounded operation inside the current burden.
- `B.s`: code/prose shorthand for burden submoves (`B.s1`, `B.s2`, ...).
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
| `fitrah` | `fitrah` | Innate normative disposition; do not reduce to culture or mood. |
| `daruri` | `daruri` | Necessary/non-discursive knowledge. |
| `nazari` | `nazari` | Discursive/inferential reasoning. |
| `wahy` | `wahy` | Revelation. |
| `shubhah` | `shubha`, plural `shubuhat` | Doubt/objection; do not route all objections as genuine shubhah before deformation/register checks. |
| `mushabara fasida` | `mushabara fasida` | False resemblance; code/data use ASCII. |
| `aqidah` | `aqidah` | Creed/doctrinal frame. |

## Smoke and Campaign Names

Named hard-smoke labels, named interlocutor labels, and comparison-standard labels are not
operative nomenclature. They may appear in fixtures, tests, smoke reports, and audit history.
Operative scripts, trigger-matrix rules, runtime governance, and public user-facing docs
should use genus-level terms such as `named source-worldview`, `imported criterion`,
`opponent worldview frame`, or `moral tribunal`.

## Release-Claim Boundary

The normalized release claim is:

- Level 3 is additive to Level 1/2.
- Codex-capable script runtimes should invoke Level 3 by default when scripts are available.
- Scriptless runtimes visibly fall back to Level 1/2.
- Routing is deterministic given extracted features.
- Feature extraction includes span-backed interpretive components and can vary.
- Transformer execution remains probabilistic and high-complexity render-through can still fail.
- Pure-Hermes parity, codons, owner packs, and catalogue-wide deterministic routing are not claimed.
