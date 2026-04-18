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
- Primary upstream issue:
- Primary deformation:
- Read status:
- Live alternatives:
- Reassessment:
- Convergence requirement:
- Discourse orientation:
- Concealment mode:
- Matched modules:
- Sequencing rationale:
- Restoration target:
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
- `Claim-type` identifies the logical category of the live pressure: `logical` (contradiction, self-defeat), `metaphysical` (existence, attribute, causation), `moral` (problem of evil, divine command, hiddenness as injustice), `historical` (manuscript, dating, provenance, authorship), `transmission` (chain-of-custody, canon formation, textual preservation), `phenomenological` (religious experience, absence of felt presence), or `authority` (who has the right to define, interpret, or adjudicate). A case can carry two types: name the primary first. This field is required because many failures come from answering one claim-type while another is doing the real governing work — a grief-case framed as logical-problem, a transmission-case framed as authority-case, or a moral-protest case framed as metaphysical argument.
- `Primary upstream issue` states the upstream issue being treated first.
- `Primary deformation` should name only the deformation governing the next move.
- `Read status` should be `dominant`, `distributed`, or `underdetermined`.
- `Live alternatives` should stay short. Keep live alternatives, not a full inventory.
- `Reassessment` should say `not warranted`, `revisit after X`, or `warranted now because Y`.
- `Convergence requirement` should say whether one dominant move remains preferable or whether
  convergence across independent routes is now needed.
- `Matched modules` should list only the matched subset. Do not advertise unused modules.
- `Sequencing rationale` should explain sequencing, not restate file names.
- `Restoration target` should say what is being cleared, restored, separated, or re-ordered.
  It names the routing-level target, not the entire restorative paragraph or closing formulation.
- `Confidence` should be marked as `strong`, `provisional`, or `low`.
- `Decisive missing differentiator` should name the one signal that would collapse the remaining ambiguity.
- `[Source Basis]` is the companion block used when the reply combines files or needs explicit
  source-status marking. Omit empty lines rather than filling every marker slot performatively.
- `Source type / weight` is optional. Use it when unlike materials are joined or when a lighter
  source is being used only for sequencing, illustration, or operational reminder rather than for
  the core doctrinal or epistemic claim.
- `Restoration source` is optional. Use it when the positive picture is being drawn from a clearly
  anchored higher-weight source rather than from free synthesis.

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

**Field discipline:**

- `Governing misread risk` names the single most likely wrong module or wrong register the case would route to without the diagnostic gate — what the skill would have done had it skipped V1 (e.g., "immediate DO-2 deployment into a grief-primary case").
- `What was withheld and why` names the module(s) held in reserve and the governing reason (grief-primary, underdetermined case, identity-performance, register not yet cleared).
- `What correction was applied` names the specific restorative move made — framework-clearing, relational register established, deformation identified and named, criterion loosened, etc.
- `Route that became permissible after correction` names what could be deployed only because the correction was made first.
- `What remains live or unresolved` names any open axis — unconfirmed deformation, live alternative, or issue whose resolution depends on the next exchange.

**Compression rule:** Populate only the fields that had operative content. A restoration trace with two populated fields is more honest than one that fills all five performatively. If no correction was required, omit the block entirely rather than filling it with null values.

**Integration with [Source Basis]:** The restoration trace is downstream of the case-state and source-basis blocks. It does not replace them. Case-state names what was diagnosed; source-basis names where claims are grounded; restoration trace names what was done to create the conditions under which the response could land.

## Strength Rules

- Mark `strong` only when multiple indicators align across noetic structure, deformation, and discourse behavior.
- Mark `provisional` when the read is plausible but still driven by partial signals.
- Mark `low` when only a thin surface objection is available and major routing dimensions remain open.

## Compression Rule

Do not narrate every field in every answer. Surface only the fields that improve governance,
legibility, or trust. The point is disciplined visibility, not transparency theater.

## Concealment × Orientation Routing Matrix

Concealment mode and DO-orient compose orthogonally. The matrix is the fastest way to see
which register the case belongs to before the doctrinal module is loaded. The matched-module
choice from the NS + deformation axis is almost always correct at the level of *content*; the
matrix answers whether the content is deployable *now* or waits on a register shift.

| Concealment \\ DO-orient | `truth-seek` | `identity-perf` | `autotelic` | `zann-mode` | `mixed` |
|--------------------------|-------------|-----------------|-------------|-------------|---------|
| — (concealment clear)    | Full apparatus. Load matched module. | Name the register first; doctrinal module waits on register shift | Do not feed; leave one question live; do not mistake for shubha | Press one specific claim at a time; suspend larger moves | Lead with the predominant orientation; note the minority channel |
| `irad`                   | Invitational register. Do not dump argument. Name the aversion; leave one honest question alive; character-as-evidence. Matched module held pending attention being given. | Iʿrāḍ compounded by identity performance hardens under argument. Relational only; no doctrinal module. | Expected compound — autotelic surface often rests on iʿrāḍ underneath. Do not feed; do not mistake for shubha. | Do not press claims; the matter has not been allowed to press. Invitation first. | Iʿrāḍ most commonly appears in mixed cases; re-enter after attention stabilizes. |
| `juhud`                  | Argument will not land. Character-as-evidence. Name the barrier (not argue past it). Doctrinal module waits. Maieutic (P4) if a seam of inner recognition is visible. | Double register-hold. Neither argument nor position-shift is available. Relational register only. | Very rare combination; usually a misread of `juhud` — often the case is actually `irad` or `istikbar`. Re-run V1. | Press one specific claim; do not supply argument that will be refused. | Treat as predominantly `juhud` unless genuine inquiry surfaces. |
| `inkar`                  | Maieutic (P4) + R2. The recognition is present; do not argue. | Identity-perf compounds the denial; pastoral register indefinite hold. | Very rare; re-run V1. | Do not press; ẓann-mode absorbs without landing. | Maieutic wins in this register more often than argument. |
| `istikbar`               | Relational + spiritual. Pride-structure is the barrier. More argument deepens it. | Compound that yields only to long relational investment. Doctrinal modules waste. | Treat as `istikbar` — the autotelic surface is usually a disguise for pride. | Rare. | Relational first in all sub-cases. |
| `nifaq`                  | Already-believing procedure (P5). Questions requiring inhabited belief. | `nifaq` + identity-perf is common; P5 with caution about what the performance is for. | Stop supplying material the performance consumes. | Very common compound; press one specific claim and require it be inhabited. | The most unstable register; re-assess frequently. |

**How to read the matrix:**
- The diagonal-like top row (concealment clear) is the only row where the full apparatus
  is deployable without register-shift concerns.
- Any non-clear concealment + `truth-seek` DO-orient means the content is right but the
  register gates access. The matched doctrinal module is held, not discarded.
- Any concealment + non-`truth-seek` DO-orient means both axes gate access; the matrix
  cell names which gate to address first.
- `mixed` DO-orient cells are always transitional; track for orientation shift and
  re-enter the matrix when it stabilizes.

**Output:** When the register-hold rule applies, include in the case-state line:

    Register-hold: <name of the axis gating access>    Deployable on shift to: <what would release the hold>

This is consumed by V1's re-run condition and by M5's register-hold field.
