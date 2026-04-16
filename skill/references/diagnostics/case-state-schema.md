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

## Strength Rules

- Mark `strong` only when multiple indicators align across noetic structure, deformation, and discourse behavior.
- Mark `provisional` when the read is plausible but still driven by partial signals.
- Mark `low` when only a thin surface objection is available and major routing dimensions remain open.

## Compression Rule

Do not narrate every field in every answer. Surface only the fields that improve governance,
legibility, or trust. The point is disciplined visibility, not transparency theater.
