---
id: M5-deformation-triage
module_class: tactic
canonical_path: skill/references/tactics/M5-deformation-triage.md
contract_version: "0.3.0.0"
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

## Role of M5 in V1

M5 is the deformation-sorting subroutine called inside V1 Phase 3 (triage). It does not
replace V1 as the entry gate. The canonical compound-case sequence lives in
`references/diagnostics/seven-deformations.md` §The Compound Case; M5 applies it.

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
