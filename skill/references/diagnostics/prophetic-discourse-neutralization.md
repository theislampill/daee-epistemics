> role: diagnostic pass — prophetic-discourse neutralization
> use when: revealed or prophetic speech is being redirected into another content, emptied of determinate meaning, or treated as non-guiding at the semantic level
> do not use when: the case is purely about transmission authenticity with no dispute over whether prophetic discourse yields determinate guidance
> output: structured detection of semantic-neutralization mode, what is being suppressed, and what must load next
> pipeline position: V1 Phase 2, after foreign-premise-detection.md when prophetic or revealed discourse is live, before doctrinal content dispatch
> paired files: foreign-premise-detection.md; prophecy-wahy-supremacy.md; V8-bila-kayf-anchor.md; do-attribute-precision.md; P3-reason-revelation-tension.md

# Prophetic Discourse Neutralization

This pass governs cases where the live move is not yet a first-order doctrinal objection but a semantic operation on prophetic discourse itself. The operation has two principal forms:

1. **Recontenting / redirection / semantic override:** the discourse is granted wording but stripped of its own semantic content and redirected into a philosophically safer content.
2. **Evacuation / agnosticism / determinate-guidance denial:** the discourse is denied any determinate semantic yield, so it can no longer guide, settle, or restore.

Both are upstream failures. They are not resolved by answering the downstream doctrinal topic while the semantic move remains unaddressed.

---

## Required Output Shape

```text
[Prophetic Discourse Neutralization]
- Status: <detected | none-detected | uncertain>
- Mode: <recontenting | evacuation | compound | none>
- Markers: <short list>
- What is being suppressed: <semantic content / guidance / predicate yield / prophetic authority>
- Evasion target: <which evidence or consequence the move avoids>
- Route consequence: <what must load next before content>
- Prohibited move: <what would ratify the neutralization>
```

When detected, record the active finding in case-state and IR as:

- `semantic-neutralization-recontenting`
- `semantic-neutralization-evacuation`

and set `Routing gate: semantic-discipline-required` until the move is addressed.

---

## Mode A — Recontenting / Redirection / Semantic Override

**Definition:** The wording is retained, but its operative content is reassigned to a different meaning judged safer by an imported framework.

**Typical markers:**
- "What the text really means is X," where X replaces the surface semantic core with a different content rather than clarifying mode.
- "Speech" becomes mere creation, decree, power, or inner meaning without showing why that replacement follows from the wording.
- Revealed predicates are kept only as rhetorical shells while the real content is transferred elsewhere.

**What it suppresses:** The determinate semantic content of the discourse and its ability to establish real divine predicates, acts, or guidance.

**What it avoids:** The need to face the revealed content on its own terms; the consequences of real divine speech, responsiveness, action, or attribute affirmation.

**Route consequence:** If a tribunal or criterion is also active, clear that first through foreign-premise-detection.md and V2. Then load the smallest semantic-restoration file that fits the case:
- V8 when the issue is divine predicate affirmation and mode
- do-attribute-precision.md when composition, predication, or perfection-smuggling is doing the work
- prophecy-wahy-supremacy.md or P3 when the move demotes prophetic authority structurally

**Prohibited move:** Accepting the redirected content as the text's real meaning and then arguing downstream from it.

---

## Mode B — Evacuation / Agnosticism / Determinate-Guidance Denial

**Definition:** The discourse is affirmed at the level of utterance but denied determinate semantic yield, so no real guidance can be taken from it.

**Typical markers:**
- "We affirm the wording but do not say what it means."
- "Prophetic speech here gives no determinate guidance beyond recitation or deference."
- "The text cannot settle this because its meaning is unknowable in principle."

**What it suppresses:** Determinate guidance, predicate yield, and the prophetic function of disclosure and clarification.

**What it avoids:** The need either to affirm the semantic core or to openly deny it; the accountability of taking the discourse as guidance-bearing.

**Route consequence:** Keep the case inside the semantic gate. Then load:
- V8 when the issue is analogical predication and mode rather than content-negation
- prophecy-wahy-supremacy.md when prophetic authority is being emptied of guiding force
- P3 when the evacuation is justified by a prior rational filter

**Prohibited move:** Treating the evacuation as piety or precision and then answering the doctrinal case as though the semantic core had been preserved.

---

## Minimal-Pair Discriminators

**Minimal pair 1 — Recontenting vs. evacuation**
- "The text means power, not mercy." → recontenting
- "We do not know what mercy means here at all." → evacuation

**Minimal pair 2 — Clarifying mode vs. neutralizing content**
- "The semantic core stands, but creaturely mode does not transfer." → V8 / analogical predication
- "The semantic core does not stand, only the wording remains." → neutralization

**Minimal pair 3 — Transmission problem vs. semantic problem**
- "Was this text authentically transmitted?" → V10 / RT family
- "Even if authentic, it yields no determinate guidance." → this file

---

## Failure Tests

This file has not governed the response if:

- The reply moves straight to the doctrinal topic while the semantic move is still live.
- Recontenting is treated as mere clarification of mode.
- Evacuation is treated as a harmless suspension of detail rather than a denial of determinate guidance.
- A case with active neutralization is surfaced with `Routing gate: open`.

---

## Mixed-Case Rule

When a semantic-neutralization move and an upstream tribunal are both live:

1. Tribunal-clearing governs intervention order.
2. The semantic-neutralization finding remains live as the next required pass.
3. Do not collapse both into one label; record both in case-state/IR.

The tribunal explains why the semantic move is being made. The neutralization pass explains how prophetic discourse is being structurally emptied inside that framework.
