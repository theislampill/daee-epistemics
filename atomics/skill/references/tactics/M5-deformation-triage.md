---
id: M5-deformation-triage
module_class: tactic
canonical_path: skill/references/tactics/M5-deformation-triage.md
contract_version: "0.4.0.0"
load_when:
  - during V1's triage phase (internal subroutine)
  - narrow single-exchange case where live question is already reduced to which deformation governs the next move
blocks:
  - NS, DO-orient, or concealment axis still under-signalled — V1 is the gate, not M5
emits:
  - deformation_type
companions:
  - V1-diagnostic
output_shapes:
  - pass-through
layer_constraint: layer-a-only
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

# M5 — Deformation Triage

## Runtime operator contract

- Activation: during V1's triage phase (internal subroutine).
- Field target: the live burden or submove pressure that made tactic `M5-deformation-triage` eligible; activation cue: during V1's triage phase (internal subroutine).
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: Layer A / diagnostic state only by default; release only the governed consequences permitted by render/output owners.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Direct routing fixtures cover this owner (14); `tools/check_routing_parity.py`, `tools/check_ttp_operator_contracts.py`, and compiled-runtime freshness must remain green.


## Role of M5 in V1

M5 is the deformation-sorting subroutine called inside V1 Phase 3 (triage). It does not
replace V1 as the entry gate. The canonical compound-case sequence lives in
`references/diagnostics/seven-deformations.md` §The Compound Case; M5 applies it.

M5 is normally Layer A diagnostic/control work: it selects the deformation read, sequencing
order, first instrument, and any register-hold. It is not a rival answer owner and not a
license to replace the matched TTP with a deformation label.

When M5 is exposed in Layer B for a narrow deformation-sorting task, activation requires:

1. target: the specific deformation signal being sorted;
2. operation: distinguish it from nearby deformation reads and select the smallest matched
   instrument;
3. result: route, hold, or hand back to V1 with the decisive missing axis named;
4. land contribution: the next owner is licensed, delayed, or blocked by the triage result.

`mushabara-fasida` is a subdeformation marker under `i'tiqadat-mawrutha`, not a standalone
argument. Marking it only licenses surgical premise work by the matched owner; it does not
itself count as M1, V2, M8, M9, or V9 execution.

## The Triage Sequence

1. Confirm the NS code from `references/diagnostics/noetic-reading-checklist.md`. The NS
   profile already implies a likely primary deformation — treat it as a prior, not as a
   conclusion.
2. Ask whether the upstream block is a general inherited *framework* (iʿtiqādāt
   mawrūtha), a habituated *pattern* (ʿāda), or a single *faulty presupposition*
   (mushābara fāsida) anchoring specific conclusions. The three are addressed differently
   and cannot be swapped.
3. Read the deformation axis per `references/diagnostics/seven-deformations.md`. Emit a
   primary deformation code or a compound pair in sequencing order (outside in).
4. Cross-check the concealment mode
   (`references/diagnostics/modes-of-concealment.md`) and DO-orient
   (`references/diagnostics/discourse-orientation.md`). If either axis is still
   under-signalled, hand the case back to V1 rather than forcing a tactic choice.
5. Select the smallest matched instrument.

## The Pairwise Sequencing Table

Compound cases are the norm. The sequence is always outside in. When two deformations
are co-present, consult the row matching the primary and the column matching the
secondary. The cell names the first move and the transition condition.

| Primary \\ Secondary | hawa | gharad | ada | i'tiqadat-mawrutha | mushabara-fasida | zann | taqlid | shubha |
|----------------------|------|--------|-----|---------------------|-------------------|------|--------|--------|
| **hawa**             | —    | F2 (acknowledge both stakes in one move) | F2 first; ʿāda waits | F2 first; V2 after volitional barrier is acknowledged | F2 first; then identify the premise | F2 first; then V7 symmetric | F2 first; then taqlīd check | F2 first; shubha last |
| **gharad**           | F2 | — | F2 first | F2 first; V2 after | F2 first; premise-targeting after | F2 first; V7 after | F2 first; taqlīd check after | F2 first; shubha last |
| **ada**              | F2 then V2+V5 | F2 then V2+V5 | — | V2 first (loosen filter), then V5 (direct attention) — ʿāda blocks V2's reach | V2 first on the framework, then surgical on the premise | V7 after V2+V5 | V7 after V2+V5 | V2+V5, then shubha |
| **i'tiqadat-mawrutha** | F2 first | F2 first | ʿāda first (V2 cannot reach under habituation) | — | Name the framework, then surgical on the specific premise | V2 and V7 in parallel | V2 and symmetric taqlīd in parallel | V2 first, shubha after |
| **mushabara-fasida** | F2 first | F2 first | ʿāda first | Framework first if general filtering is live; else surgical on the premise | — | V7 after the premise is named | Symmetric taqlīd after the premise is named | Premise first; if intellectual content remains, engage shubha |
| **zann**             | F2 first | F2 first | ʿāda first | V2 alongside V7 | Premise first | — | Symmetric taqlīd and V7 together | V7 first, shubha after |
| **taqlid**           | F2 first | F2 first | ʿāda first | V2 alongside | Premise first | V7 | — | Symmetric taqlīd first, shubha after |
| **shubha**           | F2 first; shubha is likely cover | F2 first; shubha is likely cover | ʿāda first | V2 first | Premise first | V7 first | Symmetric taqlīd first | — (engage directly: M1 / M8 / V9 as matched) |

The diagonal is empty; no deformation triages against itself. Cells above and below the
diagonal are symmetric only in compound-presence, not in intervention order — the
sequencing rule (outside in) determines which deformation is "primary" for the triage,
which is usually the one whose presence would make the other's intervention misfire.

## Concealment × Deformation Cross-Check

The deformation answers *what has suppressed the fiṭrah*; the concealment answers *what
the subject's inner/outer relation is*. The two together determine whether intellectual
content is the right register at all:

| Concealment | Deformation pairing | Register implication |
|-------------|---------------------|----------------------|
| `irad` | Any | Invitational register; do not dump argument; name the aversion; leave one honest question live; matched instrument waits on attention being given |
| `juhud` | Any | Argument will not land; character-as-evidence; name the barrier (do not argue past it); maieutic (P4) if a seam of inner recognition is visible |
| `inkar` | With hawa / gharad | Maieutic (P4) + R2; do not feed absorbable argument |
| `istikbar` | With hawa | Relational/spiritual; pride-structure is the barrier, not content |
| `nifaq` | With taqlid or zann | Already-believing procedure (P5); questions that require inhabited belief |
| `mode-?` | Any | Hand back to V1; do not commit a tactic |

If concealment is any of the first five (`irad`, `juhud`, `inkar`, `istikbar`, `nifaq`)
and the case is not `truth-seek` in DO-orient, the matched deformation instrument waits
on the register shift. M5 does not overrule the orientation read — it composes with it.

**`irad` vs. `juhud` boundary at M5:** The deformation triage is the same for both
(ʿāda/hawā still need F2, etc.), but the *register* in which the matched instrument is
delivered differs sharply. Under `irad`, the instrument is held until the subject has
let the matter press; under `juhud`, the instrument is delivered in a relational frame
that does not argue past the refusal. Misrouting between the two results in either
pressure on a non-engaged subject (argument becomes intrusion) or endless invitation to
a subject who has already moved past needing it.

## Critical Warning

Presenting intellectual content to someone whose barrier is vested interest, entrenched
will, identity-performance, or ẓann-mode discourse does not merely fail — it provides
new material for resistance or stimulation to organize around and actively hardens the
barrier. The most common failure mode in sustained epistemological engagement is
failing to triage.

## Shubhah/Shahwah Two-Axis Floor

Before treating a doubt as intellectual, distinguish:

| Axis | Corruption mode | First move | Hold |
|---|---|---|---|
| shubhah | knowledge/belief confused by an unresolved objection | clarification, proof-status, M9/V9/M1/M8 as matched | proof-stacking beyond the live objection |
| shahwah / hawa / gharad | will/aim/cost governs inquiry | F2, P1, P7, relational repair | intellectual content until the will/aim barrier is acknowledged |
| compound | both are live | outside-in sequencing; will/aim or inherited filter before shubhah | shubhah engagement until upstream layer clears |

Fitnah absorption test: if an answer is not rejected after consideration but absorbed as new
material for objection-generation, stimulation, or identity-performance, mark the case
argument-absorbent. Do not feed it with more intellectual content.

## Router Guardrails

M5 sorts deformation; it does not overrule family routing once the live case-type is
clear.
- If the presenting pressure is manuscript, canon, preservation, original-text, or
  text-history destabilization, route through V10 and the matched RT case before M5
  becomes the opening architecture.
- If the pressure is Trinity, incarnation coherence, perfect-being-to-Trinity, or
  philosopher's-God, route through V8 and the matched DO case after deformation
  sorting.
- If the pressure is a discursive attack on necessary knowledge itself, route to V9
rather than treating the issue as generic shubhah management.

## Category C Caution

The Category C note in `references/diagnostics/seven-deformations.md` is not a
first-line routing label for surface discourse. It governs suspension of pressure only
after direct evidence of cognitive inaccessibility, or after sustained engagement has
exhausted every matched instrument without a live differentiator. Never use Category C
to exit a difficult case; use it only to refuse a verdict on a person whose access is
genuinely constrained.

## Output Shape

M5 terminates with:

    Deformation: <primary> [| <secondary>]    First instrument: <matched>    Sequencing note (if compound): <what must clear before the second>    Register-hold: <none | pending-DO-orient-shift | pending-concealment-shift>

The register-hold field tells V1 whether the instrument is immediately deployable or
waits on a register shift the concealment or DO-orient axis has already flagged.
