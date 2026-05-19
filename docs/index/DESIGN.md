---
version: "alpha"
name: "DAEE docs/index"
description: "Docs/index-scoped visual identity for the generated DAEE public navigation site."
colors:
  primary: "#22C55E"
  secondary: "#98A2B3"
  tertiary: "#22D3EE"
  neutral: "#080A10"
  background: "#080A10"
  backgroundRaised: "#0F1320"
  surface: "#0C1220"
  surfaceRaised: "#141A2A"
  surfaceDeep: "#070B14"
  surfaceCode: "#0A0F1D"
  text: "#E8EDF7"
  textStrong: "#F8FAFC"
  textMuted: "#98A2B3"
  textSubtle: "#CBD5E1"
  border: "#263044"
  borderStrong: "#334155"
  focus: "#22C55E"
  info: "#60A5FA"
  success: "#22C55E"
  warning: "#FB923C"
  danger: "#F87171"
  cyan: "#22D3EE"
  violet: "#A78BFA"
  pink: "#F472B6"
  yellow: "#FACC15"
  stageD0: "#60A5FA"
  stagePsiN: "#22D3EE"
  stageDslIr: "#A78BFA"
  stageOwnerTtpDelta: "#FB923C"
  stageCollapseRestoration: "#F87171"
typography:
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.5"
    letterSpacing: "0"
  small:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: "400"
    lineHeight: "1.45"
    letterSpacing: "0"
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: "850"
    lineHeight: "1.2"
    letterSpacing: ".04em"
  heading:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "clamp(24px,2.4vw,38px)"
    fontWeight: "900"
    lineHeight: "1.08"
    letterSpacing: "-.04em"
  monospace:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: "850"
    lineHeight: "1.35"
    letterSpacing: "0"
  notation:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: "900"
    lineHeight: "1.35"
    letterSpacing: "0"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "24px"
  cardPadding: "12px"
  sectionGap: "14px"
  carouselGap: "18px"
rounded:
  chip: "999px"
  card: "10px"
  panel: "18px"
  carousel: "20px"
radius:
  chip: "999px"
  card: "10px"
  panel: "18px"
  carousel: "20px"
shadow:
  card: "0 10px 30px rgba(0,0,0,.18)"
  activeCard: "0 0 0 3px color-mix(in srgb,var(--sc),transparent 62%),0 12px 26px rgba(0,0,0,.18)"
  previewCard: "0 8px 20px rgba(0,0,0,.18)"
motion:
  duration: "200ms"
  durationFast: "150ms"
  easing: "ease"
  reducedMotion: "Disable non-essential transitions; preserve state changes without animated travel."
components:
  architectureCarousel:
    backgroundColor: "{colors.backgroundRaised}"
    borderColor: "{colors.borderStrong}"
    focusColor: "{colors.focus}"
    gap: "{spacing.carouselGap}"
    primaryWidth: "clamp(620px,52vw,860px)"
    sideWidth: "clamp(205px,13vw,300px)"
    farWidth: "clamp(56px,4vw,90px)"
    statusBackground: "{colors.surfaceDeep}"
    rounded: "{radius.carousel}"
  architectureCard:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{radius.carousel}"
    padding: "{spacing.cardPadding}"
    shadow: "{shadow.card}"
  carouselPreview:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.textSubtle}"
    opacity: ".72"
    farOpacity: ".52"
    sourceWidth: "clamp(620px,52vw,860px)"
    farSourceWidth: "clamp(620px,52vw,860px)"
    nearScale: ".34"
    farScale: ".14"
    nearSlotHeight: "560px"
    farSlotHeight: "240px"
    nearMaxHeight: "430px"
    farMaxHeight: "330px"
    shadow: "{shadow.previewCard}"
  carouselControls:
    backgroundColor: "{colors.surfaceCode}"
    textColor: "{colors.text}"
    borderColor: "{colors.borderStrong}"
    focusColor: "{colors.focus}"
    rounded: "{radius.chip}"
  pipelineRows:
    backgroundColor: "{colors.surfaceDeep}"
    borderColor: "{colors.borderStrong}"
    textColor: "{colors.text}"
    rounded: "{radius.card}"
  theoryNotation:
    backgroundColor: "{colors.surfaceCode}"
    borderColor: "{colors.borderStrong}"
    textColor: "{colors.textSubtle}"
    accentColor: "{colors.yellow}"
    rounded: "{radius.card}"
  ownerTtpMap:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.borderStrong}"
    textColor: "{colors.text}"
    rounded: "{radius.panel}"
  referenceLibrary:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    textColor: "{colors.text}"
    rounded: "{radius.panel}"
---

## Overview

This file is the docs/index-scoped visual source of truth. It follows the Google DESIGN.md pattern conservatively: machine-readable tokens live in YAML front matter, while this prose explains why those tokens exist and how generated docs/index surfaces should use them.

The generated `docs/index.html` page is not canonical. Edit this file, `docs/index/runtime-architecture.json`, source sections, templates, or generator/checker code, then rebuild.

## Visual principles

The public site should feel like an engineered diagnostic console: dense, readable, source-aware, and calm under heavy notation. Visual styling exists to improve scanability and interaction, not to imply proof, truth, warrant, uptake, or release readiness.

The Architecture carousel has one readable selected card. Side cards are compressed previews of the actual cards, preserving stage structure and identity. The Theory, Owner/TTP, and Reference Library surfaces share the same restrained system instead of becoming separate visual dialects.

## Color semantics

Background, surface, text, and border tokens establish the quiet console frame. `success`, `warning`, `danger`, and `info` are UI-state colors only. They must not imply that a runtime claim is true, warranted, restored, or behaviorally proven.

Use stage colors to distinguish runtime phases. Do not use stage color alone to encode semantic proof. Where a stage color appears, text labels, source owners, or explicit state markers must carry meaning.

## Stage color rules

The five Architecture stages use fixed visual colors:

- `stageD0`: D0 / Surface Signal.
- `stagePsiN`: PsiN / Noetic Signal-State.
- `stageDslIr`: DSL / IR & Gated Governance.
- `stageOwnerTtpDelta`: Owner/TTP + Delta / Field Diagnostics / Reread.
- `stageCollapseRestoration`: Noetic Collapse / Restoration.

These tokens own presentation only. Runtime stage meaning remains owned by `docs/index/runtime-architecture.json` and canonical atomics/runtime owners.

## Typography and notation

Body text stays compact and readable. Labels may be dense, but letter spacing should remain controlled and never become a substitute for meaning. Monospace and notation styles are for formulas, chips, pipeline rows, source paths, and compact runtime markers.

Dense formal notation must remain legible at the selected-card size. Preview cards may be too small to read fully, but they must still resemble the actual cards.

## Spacing and density

Spacing should preserve a high-density operational view while keeping cards and tables scannable. Use the spacing scale for repeated gaps, card padding, section rhythm, and carousel spacing. Do not introduce broad decorative whitespace or landing-page scale into the operational tabs.

## Design quality discipline

The visual bar is human readability, not structural validity alone. A docs/index pass can build, check, and still be visually wrong if it leaves cramped cards, generic gray panels, clipped notation, hidden interactions, or a page that only works at the author's viewport.

Before declaring visual work complete, run a source-bound design pass: confirm that repeated colors, spacing, radii, typography, focus states, and carousel dimensions come from this file or from a clearly local component rule. Runtime meaning, release status, and formal semantics must remain in their owning sources.

## Component role taxonomy

Every major tab declares surface roles with `data-surface-role` so future layout work has a visible contract:

- `focal`: the primary object a human should read or manipulate first.
- `support`: guidance, summaries, counts, or explanatory copy that helps the focal object.
- `control`: search, filter, selector, tab, carousel, notation, or card controls.
- `provenance`: source-owner material needed for auditability, but not the first reading path.
- `raw-source`: full generated tables, matrices, or source maps.
- `disclosure`: collapsed or contextual material.
- `generated-snapshot`: generated human-readable HTML preview from source-owned files.

Each of Architecture, Owners/TTP, Theory, and Reference Library should have exactly one primary focal surface. Additional cards can be useful, but they must clearly support that focal object rather than becoming a wall of equal-weight panels.

## Layout discipline

Each major section needs one primary focal object. Architecture starts with the shared runtime map, paired pipeline readings, and selected-primary carousel. Owners/TTP starts with a selected-detail operator/family workspace. Theory starts with the notation map and contextual Highlighted notation panel. Reference Library starts with source-derived counts, search/filter/list controls, and a selected generated document preview.

Use bounded grids with `minmax(0, 1fr)`, local scroll for wide tables, and wrapping text inside chips, code paths, formulas, and card bodies. Do not use page-wide horizontal chip streams when the content is a sequence; use vertical phase groups, grids, or progressive disclosure.

## Dense notation discipline

Dense notation is allowed only when it remains readable at the selected-card size. Long formulas, target grammars, source-owner lists, and path material must wrap, move into a contextual panel, or live in collapsed/provenance metadata.

Notation color inherits the Architecture phase palette. Color helps recognition, but the label, source owner, and runtime role carry meaning. Do not create symbol-only decoration, proof-by-color, or notation variants that are not source-owned.

The daee-epistemics notation is semantic material, not decorative text. Preserve exact forms such as `𝓝`, `D₀`, `Ψᴺ`, `Ψᴵ`, `N∈𝓝`, `∇·T`, `∇×T`, `ⁿBᵢ[OPᵢ]`, `ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ`, `LoopBreak(∇×T)`, `R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)`, `𝒞(Ψᴺ)`, `T_lang: Ψᴺ ⇢ Ψᴵ`, and `N_fiṭrī ∧ ʿaql ṣarīḥ`. If a layout cannot handle the notation, fix the layout; do not simplify, transliterate, rename, or ASCII-normalize the notation.

## Reference source-browser discipline

Reference Library is a source browser, not a table-first audit wall. The default path is summary counts, search/filter controls, keyboard-accessible source list, and selected generated snapshot preview. The full source map remains generated and available, but it lives in a collapsed raw-source disclosure.

Counts, paths, roles, layers, line counts, and snapshots derive from generated source data. Do not maintain parallel literal link tables.

## Owners selected-detail discipline

Owners/TTP is a selected-detail workspace. Operator/family controls and selected detail panels are the human path. Full matrices and owner/source tables remain available for audit parity, but they are collapsed or contextual by default.

Do not imply the operator graph is the full module catalogue. Operator/family maps, case-library/noetic-profile modules, and catalogue entries have distinct owners and counts.

## Carousel discipline

The Architecture carousel is a selected-primary display, not a horizontal scroll rail. One card is readable at full size. Side cards are scaled previews of the same generated cards, retaining their internal structure as previews, not separate label-only tiles.

Card changes must preserve previous/next controls, numbered selectors, side-card selection, keyboard arrow navigation, focus-visible styling, no auto-rotation, reduced-motion behavior, no-JS fallback, and print fallback.

## Interaction discipline

Interactive cards remain real controls. Visual refactors must preserve `button` semantics where present, `role`, `tabindex`, `aria-selected`, `aria-pressed`, focus rings, active styles, click handlers, keyboard handlers, and the linked detail or notation panel.

Do not flatten interactive cards into static cards to make the page easier to style. Do not replace a working interaction with a visually similar element unless the checker and browser pass prove the behavior is still present.

## Progressive disclosure discipline

Provenance, source-owner maps, full notation source maps, raw reference source maps, operator matrices, and long support tables are secondary unless the user is explicitly in an audit/source view. They should appear as contextual chips, hidden metadata, support-tab content, local scroll regions, or collapsed details, not as the dominant default reading path.

Generated HTML should be readable by humans when opened directly, but it is not canonical. Edit source files, regenerate, and let the checker guard source parity.

## Visual QA checklist

- DESIGN.md token/source-boundary pass: visuals use source-owned tokens or an intentional local component rule.
- Nielsen-style heuristic pass: primary action/status is visible, controls are predictable, layout is consistent, and recovery paths are obvious.
- WCAG/accessibility pass: keyboard operation, visible focus, semantic states, contrast, reduced motion, and responsive text all work.
- Dense-interface pass: notation, source paths, tables, chips, and formulas wrap or disclose without page-wide overflow.
- Local browser screenshot pass: view the generated page locally on desktop and a narrow/mobile width before calling visual work done.
- Poka-yoke checker pass: add or strengthen a non-brittle checker for the exact regression fixed.

## Carousel behavior

The Architecture carousel is user-controlled only:

- one selected primary card is full readable size;
- side cards are scaled/compressed previews of the actual generated cards, not label-only tiles;
- previous/next controls, dots, side-card click selection, and keyboard arrows remain available;
- no automatic rotation;
- mobile may collapse to one primary card plus controls/dots;
- print and no-JS fallback expose all cards.

## Accessibility and contrast

Focus tokens must remain visible on dark surfaces. Reduced-motion users get immediate state changes without non-essential transitions. Foreground/background token pairs are locally contrast-checked for the main text surfaces; this is a practical guard, not exhaustive accessibility certification.

## Do / Do not

Do use tokens for repeated colors, stage colors, focus rings, carousel dimensions, radii, shadows, typography families, and motion timing.

Do keep runtime semantics in `docs/index/runtime-architecture.json` and atomics/runtime owners.

Do keep one primary focal object per section and let support material stay contextual.

Do use grids, vertical lists, local scroll, wrapping, or disclosure when notation or source material gets dense.

Do run the local browser screenshot pass. Passing structural checks is not a visual pass.

Do not produce generic gray unstructured UI.

Do not make every card full-width if one selected-primary display is intended.

Do not replace scaled previews with label-only tiles.

Do not use horizontal chip streams where a grid or vertical list is needed.

Do not make provenance tables dominate the default reading path.

Do not treat passing structural checks as a visual pass.

Do not move runtime theory, owner meaning, or release evidence into this file.

Do not make side carousel cards into separate preview labels.

Do not use colors to claim truth, competence, uptake, or release proof.

Do not hand-edit generated `docs/index.html`.

Do not replace formal daee-epistemics notation with simplified labels; add plain-language labels beside or below it when needed.

Do not turn Reference Library back into a default-visible raw source table.

Do not turn Owners/TTP into a default-visible operator matrix or provenance wall.

## Source ownership

Design source: `docs/index/DESIGN.md`.

Runtime architecture source: `docs/index/runtime-architecture.json` plus declared atomics/formalism owners.

Creator: `tools/build_docs_index.py` emits generated docs surfaces and CSS custom properties.

Controller: `tools/check_docs_index_interactions.py` validates runtime/source parity, carousel behavior, and design-token boundaries.

Generated HTML is a durable artifact only after rebuild and checker pass; it is never the source of truth.
