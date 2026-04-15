# Case State Schema

> role: diagnostic-governance
> use when: any substantive response needs explicit routing state without chain-of-thought dumping
> do not use when: answering a narrow subpoint that does not require case classification
> output: compact case read, module choice, restoration target, confidence, change conditions

This file governs how the skill surfaces its read of a case. It is not a separate tactic.
It is the compact metadiscursive layer that makes routing legible and auditable.

## Standard Form

Use this block when diagnosis matters to the response:

```text
[Case State]
- Case type:
- Primary noetic issue:
- Primary deformation:
- Secondary possibilities:
- Recursion:
- Cumulative escalation:
- Discourse orientation:
- Concealment mode:
- Chosen modules:
- Why these modules:
- Restoration target:
- Confidence:
- What would change the read:
```

## Field Discipline

- `Case type` names the class of case, not the whole argument history.
- `Primary noetic issue` states the upstream issue being treated first.
- `Primary deformation` should name only the deformation governing the next move.
- `Secondary possibilities` should stay short. Keep live alternatives, not a full inventory.
- `Recursion` should say `not warranted`, `revisit after X`, or `warranted now because Y`.
- `Cumulative escalation` should say whether one dominant move remains preferable or whether
  convergence across independent routes is now needed.
- `Chosen modules` should list only the matched subset. Do not advertise unused modules.
- `Why these modules` should explain sequencing, not restate file names.
- `Restoration target` should say what is being cleared, restored, separated, or re-ordered.
- `Confidence` should be marked as `strong`, `provisional`, or `low`.
- `What would change the read` should identify the decisive missing differentiator.

## Strength Rules

- Mark `strong` only when multiple indicators align across noetic structure, deformation, and discourse behavior.
- Mark `provisional` when the read is plausible but still driven by partial signals.
- Mark `low` when only a thin surface objection is available and major routing dimensions remain open.

## Compression Rule

Do not narrate every field in every answer. Surface only the fields that improve governance,
legibility, or trust. The point is disciplined visibility, not transparency theater.
