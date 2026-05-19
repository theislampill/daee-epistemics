# docs/index Visual QA Runbook

`docs/index.html` is generated. Run this pass against the built page; do not edit the generated HTML to fix visual issues.

## Setup

```powershell
python tools\build_docs_index.py
python -m http.server 8123 --directory docs
```

Open `http://127.0.0.1:8123/index.html`.

## Every View

For each check, answer:

- What is the primary focal object?
- What is support/provenance, and is it secondary or collapsed?
- Is anything clipped?
- Is there page-wide horizontal overflow?
- Do controls work by mouse and keyboard?
- Are focus states visible?
- Is reduced-motion safe?
- Are raw tables collapsed when they are not the primary task?
- Is formal notation preserved exactly instead of simplified?

## Desktop Checks

Architecture initial:

- Focal object: runtime map, paired pipeline readings, and selected-primary carousel.
- Verify the Architecture Thesis onboards the runtime before the formal pipeline.
- Verify the paired pipelines are side-by-side vertical columns, not horizontal chip streams.
- Verify support/source-boundary prose is in compact disclosure below the focal runtime map.

Architecture card 4 selected:

- Select the Owner/TTP + Delta card.
- Verify side carousel cards are scaled previews of full cards, not label-only tiles.
- Verify dense notation such as `ⁿBᵢ[OPᵢ]`, `ΔⁿB`, `Δκ`, `∇·T`, and `∇×T` wraps without clipping.

Architecture card 5 selected:

- Select the Noetic Collapse / Restoration card.
- Verify `𝒞(Ψᴺ)`, `T_lang: Ψᴺ ⇢ Ψᴵ`, and `N_fiṭrī ∧ ʿaql ṣarīḥ` remain readable and exact.

Owners selected operator:

- Focal object: selected operator detail.
- Use search/filter and arrow/tab navigation through controls.
- Verify source-derived summaries are above raw audit tables.
- Verify operator matrix and owner/source table are collapsed by default.

Owners selected family:

- Select a family in the control layer panel.
- Verify the family detail is readable and does not compete with raw source tables.

Theory selected notation:

- Focal object: notation map plus Highlighted notation context panel.
- Select notation chips and verify the panel updates with selected notation, meaning, runtime role, source owners, and related notation.
- Verify exact notation such as `𝓝`, `D₀`, `Ψᴺ`, `Ψᴵ`, `∇`, `∇·T`, `∇×T`, `R(H,Δ)`, and `LoopBreak(∇×T)` remains unchanged.

Theory selected card:

- Select runtime notation cards in the flat execution flow.
- Verify the phase/color legend is a compact key, not a grouping mechanism.
- Verify runtime step breaks clarify sequence without repeating phase headings or turning cards into phase buckets.
- Verify cards remain buttons, focusable, and update notation highlighting.
- Verify selected notation keeps semantic color with an added active ring/glow.

Reference selected document:

- Focal object: selected generated source snapshot.
- Verify summary counts, search/filter controls, document list, and selected preview appear before provenance.
- Verify `Source map / generated provenance` is collapsed by default.

Reference Source map:

- Open the Source map disclosure.
- Verify it starts with a compact provenance summary and nested disclosures.
- Verify layer, coarse family/type, and fine-grained role/source breakdowns are compact key/value count lists, not `NAME` / `COUNT` tables or giant cards.
- Verify exact generated labels are preserved.
- Verify raw generated source rows remain a real table only inside collapsed raw provenance.

Reference filtered list:

- Filter by text and layer.
- Verify counts and list results update, selection remains visible, and no stale hand-maintained link table appears.

## Narrow / Mobile Checks

Architecture carousel:

- Verify one selected primary card is usable, controls remain reachable, and there is no page-wide horizontal overflow.

Architecture pipeline:

- Verify paired columns stack vertically and remain phase-grouped lists.

Owners controls:

- Verify search/filter, operator list, and detail stack without clipping.

Theory notation wrapping:

- Verify notation chips, formulas, card flow, legend rail, and the Highlighted notation panel wrap without replacing formal notation with simplified labels.

Reference source-browser:

- Verify source list and selected preview stack, search/filter remain keyboard usable, and raw source map stays collapsed.

## Pass/Fail Rule

Structural checks passing is not enough. A visual pass requires local browser inspection of the relevant desktop and narrow surfaces, with no major clipping, no page-wide horizontal overflow, visible focus, preserved notation, and default-collapsed provenance/raw-source material.
