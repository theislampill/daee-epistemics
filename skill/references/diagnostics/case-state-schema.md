# Case State Schema

> role: diagnostic-governance
> use when: any substantive response needs explicit routing state without chain-of-thought dumping
> do not use when: answering a narrow subpoint that does not require case classification
> output: compact case read, module choice, restoration target, confidence, change conditions

This file governs how the skill surfaces its read of a case. It is not a separate tactic.
It is the compact metadiscursive layer that makes routing legible and auditable.
Use this file as the canonical case-state shape wherever routing legibility matters.

## Standard Form

Use this block when diagnosis matters to the response:

```text
[Case State]
- Case family:
- Claim-type:
- Claim level:                      # first-order / meta-epistemic / meta-ontological / meta-noetic / cross-level; omit only when routine first-order
- Reason-category:                   # 1 / 2 / 3 / 4 - from reason-disambiguation.md; governs routing gate
- Foreign-premise status:            # detected [premise] / none-detected / uncertain - from FPD pass
- Upstream findings:                 # criterion-import / tribunal-installation / transmission-demotion / semantic-neutralization-recontenting / semantic-neutralization-evacuation / lexical-ontological-trap
- Primary upstream issue:            # must reflect FPD output when criterion-importing is live
- Pattern profile:                   # PF-1 ... PF-12 from pattern-profiling.md when a recurring cross-volume family is governing
- Primary deformation:
- Routing gate:                      # open / V2-required / deformation-first / semantic-discipline-required / register-hold / stop-condition
- Read status:
- Live alternatives:
- Reassessment:
- Convergence requirement:
- Discourse orientation:
- Concealment mode:
- Matched modules:
- Sequencing rationale:
- Restoration target:                # must name epistemic layer or ontological distinction from metaphysical-architecture.md
- Confidence:
- Decisive missing differentiator:
```

```text
[Source Basis]
- [anchored]:
- [synthesis]:
- [inference]:
- [speculative]:
- Source type / weight:
- Restoration source:
```

## Field Discipline

- `Case family` names the class of case, not the whole argument history.
- `Claim-level` is required when a higher-order burden is visible, when `cross-level` sequencing is needed, or when the full Diagnostic IR is being surfaced. In narrow routine first-order cases it may be omitted from the surfaced case-state after the diagnostic pass has found no criterion, category, or noetic-order fight. Omission means "no higher-order burden detected," not "unknown."
- `Reason-category` is required. Emit `1`, `2`, `3`, or `4` from `reason-disambiguation.md`. The routing gate depends on this field: category 3 or 4 blocks content until V2; category 2 requires deformation-first gate; category 1 leaves the gate open. Do not leave this field blank on any case where intellectual content is being pressed.
- `Foreign-premise status` is required when criterion-importing, tribunal-installation, or framework-importing elements are visible. The `[Foreign Premise Detection]` block from `foreign-premise-detection.md` feeds this field. If FPD was not run and this field is blank, the `Primary upstream issue` field cannot be reliably populated.
- `Upstream findings` is the compact owner hook for upstream burdens that must stay live across passes without collapsing into one label. Use only the canonical tags named in the standard form. When both an imported tribunal and a semantic-discipline problem are live, include both tags and let `Sequencing rationale` state the intervention order rather than erasing one into the other.
- `Primary upstream issue` must reflect FPD output when a foreign premise is live. Stating "the interlocutor doubts X" is not an upstream issue; naming the specific criterion, tribunal, or prior probability assignment that is generating the objection is.
- `Pattern profile` is optional but strongly preferred when a recurring PF family is governing the next move. Keep one primary profile only; carry competing profiles in `Live alternatives`.
- `Primary deformation` should name only the deformation governing the next move.
- `Routing gate` is required whenever any upstream blocker remains live. Use `semantic-discipline-required` when semantic neutralization or a loaded lexical-ontological trap must be cleared before doctrinal content can be released.
- `Restoration target` must name what epistemic layer (`fitrah` / sound reason / authentic transmission / inferential argument) or ontological distinction (`creator-creation` / `transcendence-immanence` / `prophetic-authority`) is being restored. A target stated as "demonstrate divine unity" or "correct the objection" has not reached the restoration level.
- `Claim-type` identifies the governing logical category of the live pressure: `logical`, `metaphysical`, `moral`, `historical`, `transmission`, `phenomenological`, or `authority`. Record the primary type only. Carry any secondary type in `Live alternatives`, `[Core Formulation]`, or `What remains live`.
- `Read status` should be `dominant`, `distributed`, or `underdetermined`.
- `Live alternatives` should stay short. Keep live alternatives, not a full inventory.
- `Reassessment` should say `not warranted`, `revisit after X`, or `warranted now because Y`.
- `Convergence requirement` should say whether one dominant move remains preferable or whether convergence across independent routes is now needed.
- `Matched modules` should list only the matched subset. Do not advertise unused modules.
- `Sequencing rationale` should explain sequencing, not restate file names.
- `Confidence` should be marked as `strong`, `provisional`, or `low`.
- `Decisive missing differentiator` should name the one signal that would collapse the remaining ambiguity.
- `[Source Basis]` is the companion block used when the reply combines files or needs explicit source-status marking. Omit empty lines rather than filling every marker slot performatively.
- `Source type / weight` is optional. Use it when unlike materials are joined or when a lighter source is being used only for sequencing, illustration, or operational reminder rather than for the core doctrinal or epistemic claim.
- `Restoration source` is optional. Use it when the positive picture is being drawn from a clearly anchored higher-weight source rather than from free synthesis.

## Restoration Trace Block

Use this block after the matched-module response is complete. It records the restorative logic, not just the argumentative content. Omit when the case is too thin for restorative work to have been performed, or when the routing was entirely routine.

```text
[Restoration Trace]
- Governing misread risk:
- What was withheld and why:
- What correction was applied:
- Route that became permissible after correction:
- What remains live or unresolved:
```

Field discipline:

- `Governing misread risk` names the single most likely wrong module or wrong register the case would route to without the diagnostic gate.
- `What was withheld and why` names the module(s) held in reserve and the governing reason.
- `What correction was applied` names the specific restorative move made.
- `Route that became permissible after correction` names what could be deployed only because the correction was made first.
- `What remains live or unresolved` names any open axis, unconfirmed deformation, or live alternative.

Compression rule: populate only the fields that had operative content. A restoration trace with two populated fields is more honest than one that fills all five performatively. If no correction was required, omit the block entirely.

Integration with `[Source Basis]`: the restoration trace is downstream of the case-state and source-basis blocks. It does not replace them. Case-state names what was diagnosed; source-basis names where claims are grounded; restoration trace names what was done to create the conditions under which the response could land.

## Strength Rules

- Mark `strong` only when multiple indicators align across noetic structure, deformation, and discourse behavior.
- Mark `provisional` when the read is plausible but still driven by partial signals.
- Mark `low` when only a thin surface objection is available and major routing dimensions remain open.

## Compression Rule

Do not narrate every field in every answer. Surface only the fields that improve governance, legibility, or trust. The point is disciplined visibility, not transparency theater.

## Concealment x Orientation Routing Matrix

Concealment mode and DO-orient compose orthogonally. The matrix is the fastest way to see which register the case belongs to before the doctrinal module is loaded. The matched-module choice from the NS + deformation axis is almost always correct at the level of content; the matrix answers whether the content is deployable now or waits on a register shift.

| Concealment \\ DO-orient | `truth-seek` | `identity-perf` | `autotelic` | `zann-mode` | `mixed` |
|--------------------------|-------------|-----------------|-------------|-------------|---------|
| clear | Full apparatus. Load matched module. | Name the register first; doctrinal module waits on register shift. | Do not feed; leave one question live; do not mistake for shubha. | Press one specific claim at a time; suspend larger moves. | Lead with the predominant orientation; note the minority channel. |
| `irad` | Invitational register. Do not dump argument. Name the aversion; leave one honest question alive; character-as-evidence. Matched module held pending attention being given. | `irad` compounded by identity performance hardens under argument. Relational only; no doctrinal module. | Expected compound; do not feed; do not mistake for shubha. | Do not press claims; the matter has not been allowed to press. Invitation first. | Re-enter after attention stabilizes. |
| `juhud` | Argument will not land. Character-as-evidence. Name the barrier, not argument past it. Doctrinal module waits. Maieutic if a seam of inner recognition is visible. | Double register-hold. Relational register only. | Usually a misread; re-run V1. | Press one specific claim; do not supply argument that will be refused. | Treat as predominantly `juhud` unless genuine inquiry surfaces. |
| `inkar` | Maieutic (P4) + R2. Recognition is present; do not argue. | Identity-performance compounds the denial; pastoral register indefinite hold. | Very rare; re-run V1. | Do not press; `zann-mode` absorbs without landing. | Maieutic wins here more often than argument. |
| `istikbar` | Relational + spiritual. Pride-structure is the barrier. More argument deepens it. | Compound that yields only to long relational investment. Doctrinal modules waste. | Treat as `istikbar`; the autotelic surface is usually a disguise for pride. | Rare. | Relational first in all sub-cases. |
| `nifaq` | Already-believing procedure (P5). Questions requiring inhabited belief. | Common compound; P5 with caution about what the performance is for. | Stop supplying material the performance consumes. | Very common compound; press one specific claim and require it be inhabited. | Re-assess frequently. |

How to read the matrix:

- The top row is the only row where the full apparatus is deployable without register-shift concerns.
- Any non-clear concealment + `truth-seek` means the content may be right but the register gates access. The matched doctrinal module is held, not discarded.
- Any concealment + non-`truth-seek` means both axes gate access; the cell names which gate to address first.
- `mixed` DO-orient cells are transitional; track for orientation shift and re-enter the matrix when it stabilizes.

Output: when the register-hold rule applies, include in the case-state line:

```text
Register-hold: <name of the axis gating access>    Deployable on shift to: <what would release the hold>
```

This is consumed by V1's re-run condition and by M5's register-hold field.
