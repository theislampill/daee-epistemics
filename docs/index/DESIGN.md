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
  carouselGap: "10px"
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
    sideWidth: "clamp(150px,12vw,190px)"
    farWidth: "clamp(48px,4vw,60px)"
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
    sourceWidth: "440px"
    farSourceWidth: "440px"
    nearScale: ".43"
    farScale: ".14"
    nearSlotHeight: "330px"
    farSlotHeight: "150px"
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

Do not move runtime theory, owner meaning, or release evidence into this file.

Do not make side carousel cards into separate preview labels.

Do not use colors to claim truth, competence, uptake, or release proof.

Do not hand-edit generated `docs/index.html`.

## Source ownership

Design source: `docs/index/DESIGN.md`.

Runtime architecture source: `docs/index/runtime-architecture.json` plus declared atomics/formalism owners.

Creator: `tools/build_docs_index.py` emits generated docs surfaces and CSS custom properties.

Controller: `tools/check_docs_index_interactions.py` validates runtime/source parity, carousel behavior, and design-token boundaries.

Generated HTML is a durable artifact only after rebuild and checker pass; it is never the source of truth.
